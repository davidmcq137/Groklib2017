#simple stripchart using pygame
import pygame, math, random                   
white=(255,255,255)                             #define colors                      
red=(255,0,0)
pygame.init()                                   #initialize pygame
width=1000
height=200
size=[width,height]                             #select window size
screen=pygame.display.set_mode(size)            #create screen
pygame.display.set_caption("Python Strip Chart")
clock=pygame.time.Clock()
data=[]
for x in range (0,width+1):
        data.append([x,100])

# -------- Event Loop -----------
while (not pygame.event.peek(pygame.QUIT)):     #user closed window
        for x in range (0,width):
                data[x][1]=data[x+1][1]       #move points to the left
        t=pygame.time.get_ticks()            #run time in milliseconds
        noise=random.randint(-10,10)         #create random noise
        data[width][1]=100.-50.*math.sin(t/200.) +noise #new value
        screen.fill(white)                         #erase the old line
        pygame.draw.lines(screen, red, 0,data,3)   #draw a new line
        clock.tick(150)                            #regulate speed
        pygame.display.flip()                  #display the new screen
pygame.quit ()                                #exit if event loop ends
