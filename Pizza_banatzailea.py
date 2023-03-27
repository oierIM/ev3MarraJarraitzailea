#!/usr/bin/env python3

from pickle import TRUE
from ev3dev2.sensor import Sensor,INPUT_1,INPUT_3,INPUT_2,INPUT_4
from time import sleep
from ev3dev2.motor import OUTPUT_A, OUTPUT_D, MoveTank, LargeMotor
from threading import Thread
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
import time 



class marraJarraitu(Thread): ##Marra jarraitzaile klasea
    def __init__(self, threadID): #Eraikitzailea
        Thread.__init__(self)
        self.threadID = threadID
        self.lsa = Sensor(INPUT_3) #3.Outputetik lsa sentsorea hartu
        self.running = True

        self.v_base = 20 #Oinarrizko abiadura
        self.vl = 20 #Ezker gurpilaren abiadura
        self.vr = 20 #Eskuin gurpilaren abiadura



    def printLSA(self):
        for i in range(0,8):
            print("i=%d value=%d"%(i, self.lsa.value(i)))
        print("--------------------------------")


    def lortu_minimoak(self): #Bi balio minimoak eta ea atera den itzultzen du
        atera_Da = False
        if self.lsa.value(0)<self.lsa.value(1): #Lehen irakurketa
            min1=self.lsa.value(0)
            in1=0
            min2=self.lsa.value(1)
            in2=1
        else:
            min1=self.lsa.value(1)
            in1=1
            min2=self.lsa.value(0)
            in2=0
        
        for i in range(2,8):
            if self.lsa.value(i)<min1: 
                lag=min1
                in2=in1
                min2=lag
                min1=self.lsa.value(i)
                in1=i
            elif(self.lsa.value(i)<min2):
                min2=self.lsa.value(i)
                in2=i
        if min1 > 25: #Dena txuria bada atera dela
            atera_Da = True
        return (in1+in2)/2 , atera_Da #Bi balio minimoen indizeen bataz bestekoa itzuli

    def run(self): #Vr eta Vl aldagai globalei abiadura balioak esleitzen zaizkie
        desbiderapena = 0

        while self.running:
            while True: 
                desbiderapena, atera = self.lortu_minimoak() #Deitu aurreko funtzioari
                desbiderapena-=3.5 #Erdi puntuarekiko desbiderapena lortu

                if desbiderapena <0: #Negatiboa bada (eskuinerantz)
                    desbiderapena = abs(desbiderapena)
                    self.vl = self.v_base+desbiderapena*4 #Abiadura gehitu
                    self.vr = self.v_base-desbiderapena*2 #Abiadura kendu
                elif desbiderapena >0: #Positiboa bada (ezkerrerantz)
                    self.vr = self.v_base+desbiderapena*4 #Abiadura gehitu
                    self.vl = self.v_base-desbiderapena*2 #Abiadura kendu
                else: #Zuzen badoa abiadura handitu
                    self.vl =self.v_base+10 
                    self.vr =self.v_base+10
                if atera:
                    self.vl+=15 #Atera ezkero eskuinerantz birak eman
                sleep(0.01)


class bideGurutzeDetektatu(Thread): #Bidegurutzeak detektatu kolore sentsorearekin
    def __init__(self, threadID):
        Thread.__init__(self)
        self.threadID = threadID
        self.beltzaDago = False

    def run(self):
        cs = ColorSensor(INPUT_4) #Sentsorea hartu 4.inputetik            
        while True:
            red = cs.rgb[0] #Koloreak hartu
            green = cs.rgb[1]
            blue = cs.rgb[2]
            batura=red+green+blue #Hiru koloreen balioen batura hartu
            if batura<50: #Esan nahi du sentsoreak beltza irakurri duela (bidegurutzea dagoela)
                self.beltzaDago=True #Aldagai globalari balioa esleitu
                sleep(2) 
            else: #Ez dago bidegurutzea
                self.beltzaDago = False
            sleep(0.1)

class semaforoIdentifikatu(Thread): #Zein semaforotan gauden identifikatzen du
    def __init__(self, threadID, order):
        Thread.__init__(self)
        self.threadID = threadID
        self.running = True
        self.order = order #Semaforoen ordena ematen da
        self.bide_atera = False
        self.semaforo=False
        



    def run(self):
        cs = ColorSensor(INPUT_4) #Kolore sentsorea irakurri 4.inputetik
        kol_list = [] #Semaforo lista hasieratu
        self.belzaDago=False
        ezdagored = False #Kolore bakoitza ea ez dagoen adierazten dute
        ezdagogreen = False
        ezdagoblue = False
        while len(self.order)>0: #Semaforo guztiak irakurri arte

            red = cs.rgb[0]
            green = cs.rgb[1]
            blue = cs.rgb[2]

            if max(red,green,blue) == red and red > 35 and green <20 and blue <25 and not ezdagored: #Gorri kolorearen baldintzak
                kol_list.append("R") 
                ezdagored = True

            elif max(red,green,blue) == blue and blue >55 and red <25 and green > 25 and  not ezdagoblue: #Urdin kolorearen baldintzak
                kol_list.append("B")
                ezdagoblue = True

            elif (max(red,green,blue) == blue or max(red,green,blue) == green) and green>40 and blue>40 and green>red and red <55 and not ezdagogreen: #Berde kolorearen baldintzak
                kol_list.append("G")
                ezdagogreen = True

   

            if len(kol_list)==3: #3 kolore desberdin irakurritakoan (semaforo osoa irakurri du)
                semaforoa=-1
                col = self.order[0][0]
                pos = int(self.order[0][1])
                # self.order ek irakurritako koloreak eta haien posizioa zein izan den esango digu
                if "G1" in self.order or "B2" in self.order or "R3" in self.order: #Zein semaforotan gauden ikusi
                    semaforoa=1
                elif "R1" in self.order or "G2" in self.order or "B3" in self.order:
                    semaforoa=2
                else: semaforoa =3
                
                if kol_list[pos-1] == col: #Semaforo honetan atera behar du
                    self.semaforo = True
                    self.bide_atera = True
                    self.order.pop(0)
                    kol_list = []
                    if semaforoa==1 or semaforoa==3:sleep(10) #Semaforoaren arabera sleep ak aldatu
                    else:sleep(14)
                else: #Ez du irten behar
                    self.semaforo = True
                    sleep(6)
                
                #Aldagaiak hasieratu hurrengo irakurketarako
                self.semaforo = False
                self.bide_atera = False
                kol_list = []
                garbiketa = 0
                ezdagogreen = False
                ezdagored = False
                ezdagoblue = False
            
            sleep(0.4)


class TalkaEkidin(Thread): #Talka ekiditeko hariaren definizioa
    def __init__(self, threadID):
        Thread.__init__(self)
        self.threadID = threadID
        self.running = True
        self.talkaDago = 1



    def run(self):
        us = UltrasonicSensor() #Sentsorea hartu
        while True:
            if us.distance_centimeters < 25: #Oztopo bat badago
                self.talkaDago = 0
            else: #Ez badago
                self.talkaDago = 1
            sleep(0.4)



if __name__ == "__main__":

    orderlist = ["R2","G1","B3"] #Semaforoen ordena finkatu
    robot = MoveTank(OUTPUT_A, OUTPUT_D) 
    
    #HARIEN HASIERAKETA
    
    #Marra jarraitzailea
    mj_t = marraJarraitu(1)
    mj_t.setDaemon = True
    mj_t.start()
    
    #Semaforoen identifikatzailea
    si_t = semaforoIdentifikatu(2, orderlist)
    si_t.setDaemon = True
    si_t.start()
    
    #Talka ekidin
    te_t = TalkaEkidin(3)
    te_t.setDaemon = True
    te_t.start()

    #Bidegurutzeen detekzioa
    bd_t = bideGurutzeDetektatu(4)
    bd_t.setDaemon(True)
    bd_t.start()

    running = True
    while running:
        #Marra jarraitzailearen balioak hartu
        vl = mj_t.vl
        vr = mj_t.vr
        #Zuzenketa aplikatu bidegurutzeak nahigabe ez hartzeko
        vl-=12
        vr-=5

        if si_t.semaforo: #Semaforo bat topatu ezkero motelago joan
            vl -= 5
            vr -= 5
            
        if si_t.bide_atera: #Semaforoa hartu behar badu
            vr-=7 #Bidegurutzeentzat aplikatutako zuzenketa anulatu
            if bd_t.beltzaDago: #Sentsoreak beltza ikusten duen bitartean eskuinerantz bira egin
                vl=10
                vr=0

        #Parean objeturenbat dagoen bitartean gelditu
        vl *= te_t.talkaDago
        vr *= te_t.talkaDago


        robot.on(vl, vr)
        sleep(0.01)