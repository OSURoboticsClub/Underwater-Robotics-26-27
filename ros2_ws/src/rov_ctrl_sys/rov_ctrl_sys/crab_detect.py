import rclpy
from rclpy.signals import SignalHandlerOptions
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor

from sensor_msgs.msg import Image
from std_msgs.msg import String

import threading
import pathlib
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class CrabDetect(SubscriberPublisher):

    def __init__(self):
        super().__init__('crab_detect', Image, 'image_raw', Image, 'image_processed', 1, 1)

        key_qos = QoS.QoSProfile(
            depth=10, 
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        self.sub_keys = self.create_subscription(
                String, 
                'key_states', 
                self.key_callback, 
                key_qos
        )

        self.detecting = False
        self.detect_lock = threading.Lock()
        self.p_pressed = False

        self.crab_path = str(pathlib.Path.home()) + '/Underwater-Robotics-Current/crab_detect/'
        self.model_path = self.crab_path + 'best_lightblur.pt'
        self.model_trained = YOLO(self.model_path)
        self.model_trained.to('cpu')

        self.bridge = CvBridge()


    def key_callback(self, msg):
        keys = set(msg.data.split(','))
        if not self.p_pressed and 'P' in keys:
            self.p_pressed = True
            with self.detect_lock:
                self.detecting = not self.detecting
        elif self.p_pressed and 'P' not in keys:
            self.p_pressed = False


    def generate_pub_msg(self, msg):
        with self.detect_lock:
            detecting = self.detecting

        if msg:
            if detecting:
                frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                # Run prediction
                results = self.model_trained.predict(source=frame, conf=0.3, iou=0.45, verbose=False)


                # ==========================================
                # REVISED RESULT PARSING (From your image)
                # ==========================================
                font = cv2.FONT_HERSHEY_SIMPLEX
                height = 12
                font_size = cv2.getFontScaleFromHeight(font, height,2)
                pos = (5,5+height)

                for r in results:
                    # CHANGED: Use r.obb instead of r.boxes for Oriented Bounding Box models
                    boxes = r.obb 
                    classes = r.names 
                    
                    # SAFETY CHECK: Only try to count/loop if boxes actually exist
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0]) 
                            class_name = classes[class_id]
                            confidence = float(box.conf[0])
                    # Loop through every individual box found in this frame
                # ==========================================

                    # Draw the bounding boxes on the image
                    crab_count = len(results[0].obb) if results[0].obb is not None else 0
                    txt = f'Invasive Crabs Found: {crab_count}'
                    size = cv2.getTextSize(txt, font, font_size, 2)
                    annotated_frame = results[0].plot(labels=False, conf=False)
                    annotated_frame = cv2.rectangle(annotated_frame, (pos[0]-2,pos[1]+3), (pos[0]+size[0][0], pos[1]-size[0][1]-1), (0,0,0), cv2.FILLED)
                    annotated_frame = cv2.putText(annotated_frame, txt, pos, font, font_size, (255,255,255), 2)
                    current_display_frame = annotated_frame
                    # Update the live window with the new boxed frame

                return_msg = self.bridge.cv2_to_imgmsg(current_display_frame, encoding='rgb8')

#                 self.get_logger().info('hello_world')
                return return_msg
            else:
                return msg
        else:
            return None

def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = CrabDetect()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (SIGINT)")
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
