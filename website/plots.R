# ensure libraries exist in environment
if (!require("fmsb")) install.packages("fmsb", repos = "https://cloud.r-project.org")
if (!require("ggplot2")) install.packages("ggplot2", repos = "https://cloud.r-project.org")

library(fmsb)
library(ggplot2)
#/Users/oliverchanschatz/Documents/CE Economy Research/Web App/website/static/index_data.csv

args = commandArgs(trailingOnly=TRUE)
csv_path = args[1]
output_dir = args[2]

df = read.csv(csv_path)

latest = df[nrow(df), c("index_energy", "index_water", "index_emissions", "index_waste")]
radar_data = rbind(rep(1, 4), rep(0, 4), latest)
colnames(radar_data) = c("Energy", "Water", "Emissions", "Waste")
print(radar_data)

spider_path = file.path(output_dir, "generated_spider.png")
png(spider_path, width = 600, height = 600)

radarchart(radar_data,
           axistype = 1, # center axis label only
           pcol = "#c5050c", # data color
           pfcol = adjustcolor("#c5050c", alpha.f = 0.4), # fill color
           plwd = 4, # line width
           cglcol = "grey",
           cglty = 1, # solid line
           axislabcol = "#065465",
           caxislabels = c(0, 0.25, 0.5, 0.75, 1),
           cglwd = 0.8,
           vlcex = 1.2)
dev.off()

timeseries_path = file.path(output_dir, "generated_timeseries.png")
png(timeseries_path, width = 800, height = 500)
ggplot(df, aes(x = year, y = CE_Index)) +
  geom_line(color = "#9b0000", size = 1.2) +
  geom_point(size = 3, color = "#c5050c") +
  theme_minimal() +
  theme(axis.text = element_text(size = 20)) +
  #labs(y = "CE Index", x = "Year") +
  labs(y = "", x = "") +
  scale_x_continuous(breaks = df$year)
dev.off()