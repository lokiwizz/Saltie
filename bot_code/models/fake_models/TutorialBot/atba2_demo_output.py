import math
import tensorflow as tf

pi = 3.141592653589793
U = 32768.0

class TutorialBotOutput:

    def __init__(self, batch_size):
        self.batch_size = batch_size
        global zero,zeros3
        zero = tf.zeros(self.batch_size, tf.float32)
        zeros3 = [zero,zero,zero]

    def get_output_vector_model(self, state_object):

        steer = pitch = yaw = roll = throttle = boost = jump = powerslide = zero

        player, ball = state_object.gamecars[0], state_object.gameball

        pL,pV,pR,paV,pB = a3(player.Location), a3(player.Velocity), a3(player.Rotation), a3(player.AngularVelocity), tf.cast(player.Boost,tf.float32)
        bL,bR,bV = a3(ball.Location), a3(ball.Rotation), a3(ball.Velocity)

        pxv, pyv, pzv = local(pV,zeros3,pR)
        iv,rv,av = local(paV,zeros3,pR)

        tx, ty, tz = local(bL,pL,pR)
        txv, tyv, tzv = local(bV,zeros3,pR)
        xv, yv, zv = pxv-txv, pyv-tyv, pzv-tzv

        dT = (.5*tf.abs(ty) + 0.9*tf.abs(tx) + .34*tf.abs(tz))/1500.0
        tLV = bL + bV * dT

        x,y,z = local(tLV,pL,pR)
        d,a,i = spherical(x,y,z)
        r = pR[2]/U

        # controlls
        throttle = bucket((y-yv*.2)/900.0)
        steer = bucket((a-av/45.0)/2.0)
        yaw = bucket((a-av/13.0)/2.0)
        pitch = bucket(-i-iv/15.0)
        roll = bucket(-r+rv/22.0)

        boost = tf.cast( tf.logical_and( tf.greater(.15,tf.abs(a)), tf.logical_and( tf.greater(throttle,0), tf.greater(tf.abs(.5-tf.abs(i)),.25) )) ,tf.float32)
        powerslide = tf.cast( tf.logical_and( tf.greater(throttle*pyv,0.0),
                                              tf.logical_and( tf.greater(tf.abs(a-av/35.0),.2),
                                                              tf.logical_and( tf.greater(.8,tf.abs(a-av/35.0)),
                                                                              tf.greater(xv,500.0) ) ) ) ,tf.float32)

        output = [throttle, steer, pitch, yaw, roll, jump, boost, powerslide]

        return output

def a3(V):
    try : a = tf.stack([V.X,V.Y,V.Z])
    except :
        try :a = tf.stack([V.Pitch,V.Yaw,V.Roll])
        except : a = tf.stack([V[0],V[1],V[2]])
    return tf.cast(a,tf.float32)

def Range180(value,pi):
    value = value - tf.abs(value)//(2.0*pi) * (2.0*pi) * tf.sign(value)
    value = value - tf.cast(tf.greater( tf.abs(value), pi),tf.float32) * (2.0*pi) * tf.sign(value)
    return value

def rotate2D(x,y,ang):
    x2 = x*tf.cos(ang) - y*tf.sin(ang)
    y2 = y*tf.cos(ang) + x*tf.sin(ang)
    return x2,y2

def local(tL,oL,oR,Urot=True):
    L = tL-oL
    if Urot :
        pitch = oR[0]*pi/U
        yaw = Range180(oR[1]-U/2,U)*pi/U
        roll = oR[2]*pi/U
        R = -tf.stack([pitch,yaw,roll])
    else :
        R = -oR
    x,y = rotate2D(L[0],L[1],R[1])
    y,z = rotate2D(y,L[2],R[0])
    x,z = rotate2D(x,z,R[2])
    return x,y,z

def spherical(x,y,z):
    d = tf.sqrt(x*x+y*y+z*z)
    try : i = tf.acos(z/d)
    except: i=0
    a = tf.atan2(y,x)
    return d, Range180(a-pi/2,pi)/pi, Range180(i-pi/2,pi)/pi

def d3(A,B=[0,0,0]):
    A,B = a3(A),a3(B)
    return tf.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)

def bucket(a):
    cond1 = tf.cast(abs(a)> .2, tf.float32)
    result = cond1*tf.sign(a) + (1-cond1)*.5*tf.sign(a)
    cond2 = tf.cast(abs(a)>.01, tf.float32)
    result = cond2*result
    return result
