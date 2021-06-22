# Test file for Ralph with plot returned as raw file
#
# Author: yanabr
###############################################################################

rm(list=ls())
graphics.off()

pid <- Sys.getpid()

## some dummy data
x <- sort(rnorm(100))
y <- 2*x+rnorm(100,0,0.5)

## model
model <- lm(y~x)

filename <- paste('plot_',pid,'.png',sep="")
png(width=480, height=480, file=filename)
plot(x,y)
abline(coef(model),col=2,lty=2)
dev.off()

im <- readBin(filename,"raw", 999999)

result_vector <- list(x,y,coef(model),im)
