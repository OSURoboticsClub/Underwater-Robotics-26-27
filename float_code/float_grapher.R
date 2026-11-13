library(openintro)
library(tidyverse)
library(broom)

file_path <- if (file.exists("float-testing.txt")) "float-testing.txt" else file.choose()
float_data <- read.csv(file_path)

our_float <- float_data %>%
  filter(name == "EX31") %>%
  select(-name)

ggplot(data = our_float, aes(x = time, y = depth)) + 
  geom_point() +
  labs(x = "Time (ms since float power on",
       y = "Depth (m)") 