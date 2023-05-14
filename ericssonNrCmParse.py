#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:haojian
# File Name: ericssonNrCmParse.py
# Created Time: 2022-6-22 19:32:52
# cm文件位置：/data/esbftp/cm/5G/ERICSSON/OMC1/CM/20220627/CM_5G_A1_20220627010000_000.TAR.GZ


import os,sys
import logging
from logging.handlers import RotatingFileHandler
import xml.etree.ElementTree as ET
import datetime
import re
import math
import tarfile
import glob

os.chdir(sys.path[0])
#assert ('linux' in sys.platform), '该代码只能在 Linux 下执行'
if 'linux' in sys.platform:
    inpath='/data/esbftp/cm/5G/ERICSSON/OMC1/CM/%s/CM_5G_A1_*.TAR.GZ'%datetime.datetime.now().strftime('%Y%m%d')
    outpath1='./'
    outpath2='/data/output/cm/ericsson/5g/'
    logpath='../log/'
else:
    inpath='./CM_5G_A1_*.TAR.GZ'
    outpath1='./'
    outpath2='./'
    logpath='./'

#handler = RotatingFileHandler('cmParse.log',maxBytes = 100*1024*1024,backupCount = 3)
handler = logging.FileHandler(logpath+'ericssonNrCmParse_'+datetime.datetime.now().strftime("%Y%m%d")+'.log')
#handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console = logging.StreamHandler()
#console.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
logger.addHandler(handler)
if 'linux' not in sys.platform:
    logger.addHandler(console)


def fcn2feq(fcn):
    #LTE根据频点计算频率
    fcn=int(fcn)
    if fcn<600:	
        ful=1920+0.1*(fcn-0);fdl=ful+190
    elif fcn<1200:	
        ful=1850+0.1*(fcn-600);fdl=ful+80
    elif fcn<1950:	
        ful=1710+0.1*(fcn-1200);fdl=ful+95
    elif fcn<2400:	
        ful=1710+0.1*(fcn-1950);fdl=ful+400
    elif fcn<2650:	
        ful=824+0.1*(fcn-2400);fdl=ful+45
    elif fcn<2750:	
        ful=830+0.1*(fcn-2650);fdl=ful+45
    elif fcn<3450:	
        ful=2500+0.1*(fcn-2750);fdl=ful+120
    elif fcn<3800:	
        ful=880+0.1*(fcn-3450);fdl=ful+45
    elif fcn<4150:	
        ful=1749.9+0.1*(fcn-3800);fdl=ful+95
    elif fcn<4750:	
        ful=1710+0.1*(fcn-4150);fdl=ful+400
    elif fcn<5000:	
        ful=1427.9+0.1*(fcn-4750);fdl=ful+48
    elif fcn<5180:	
        ful=698+0.1*(fcn-5000);fdl=ful+30
    elif fcn<5280:	
        ful=777+0.1*(fcn-5180);fdl=ful+-31
    elif fcn<5380:	
        ful=788+0.1*(fcn-5280);fdl=ful+-30
    elif fcn<5850:	
        ful=704+0.1*(fcn-5730);fdl=ful+30
    elif fcn<6000:	
        ful=815+0.1*(fcn-5850);fdl=ful+45
    elif fcn<6150:	
        ful=830+0.1*(fcn-6000);fdl=ful+45
    elif fcn<6450:	
        ful=832+0.1*(fcn-6150);fdl=ful+-41
    elif fcn<6600:	
        ful=1447.9+0.1*(fcn-6450);fdl=ful+48
    elif fcn<7400:	
        ful=3410+0.1*(fcn-6600);fdl=ful+100
    elif fcn<7700:	
        ful=2000+0.1*(fcn-7500);fdl=ful+180
    elif fcn<8040:	
        ful=1626.5+0.1*(fcn-7700);fdl=ful+-101.5
    elif fcn<8690:	
        ful=1850+0.1*(fcn-8040);fdl=ful+80
    elif fcn<9040:	
        ful=814+0.1*(fcn-8690);fdl=ful+45
    elif fcn<9210:	
        ful=807+0.1*(fcn-9040);fdl=ful+45
    elif fcn<9660:	
        ful=703+0.1*(fcn-9210);fdl=ful+55
    else:
        ful=0;fdl=0
    return ful,fdl

def deal_with_file(f,sdate,csvList):
    out=dict()
    fdn=[]
    while True:
        l=f.readline().decode()
        if l.startswith('FDN : ') and fdn != []:
            if re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,ENodeBFunction=1,EUtranCellFDD=[^,]+"',fdn[0].strip()):
                logger.info("LTE小区名："+fdn[0].strip().split(':')[1].strip('"').split(',')[4])
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBDUFunction=[^,]+,NRCellCU=[^,]+"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                NRCell=fdn_['FDN'].strip('"').split(',')[-1].split('=')[1]
                out[NRCell].update(fdn_) if NRCell in out else out.update({NRCell:fdn_})
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBDUFunction=[^,]+,NRCellDU=[^,]+"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                #基本小区参数
                NRCell=fdn_['FDN'].strip('"').split(',')[-1].split('=')[1]
                out[NRCell].update(fdn_) if NRCell in out else out.update({NRCell:fdn_})
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBCUCPFunction=[^,]+,EndpointResource=[^,]+,LocalSctpEndpoint=[^,]+"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                #用于确认组网类型 即部署模式 爱立信贾工说都是SA，这项暂时不解析
                interfaceUsed=fdn_['interfaceUsed']
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBCUCPFunction=[^,]+,NRCellCU=[^,]+,AdditionalPLMNInfo=1"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                #用于确认小区是否共享小区
                NRCell=fdn_['FDN'].strip('"').split(',')[4].split('=')[1]
                out[NRCell].update({'share':'1'}) if NRCell in out else out.update({NRCell:{'share':'1'}})
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBDUFunction=1,NRSectorCarrier=[^,]+"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                try:
                    NRCell=eval(fdn_['reservedBy'])[0].strip('"').split(',')[-1].split('=')[1]
                except:
                    print(fdn)
                    print(fdn_)
                    print(fdn_['reservedBy'])
                if fdn_['reservedBy']!='<empty>':
                    NRCell=eval(fdn_['reservedBy'])[0].strip('"').split(',')[-1].split('=')[1]
                    out[NRCell].update(fdn_) if NRCell in out else out.update({NRCell:fdn_})
            elif re.match(r'FDN : "SubNetwork=[^,]+,MeContext=[^,]+,ManagedElement=[^,]+,GNBCUCPFunction=[^,]+"',fdn[0].strip()):
                fdn_=dict([i.split(' : ') for i in fdn])
                gNBId=fdn_['gNBId']
            fdn=[]
        if l=='\n':
            continue
        elif l=='':
            break
        else:
            fdn.append(l.strip())
    for NRCell in out:
        #sdate=''                        #分析时间
        isalive='1'                        #是否在网
        islock='0' if out[NRCell]['administrativeState']=='UNLOCKED' else '1'                        #是否闭锁，只要不是unlock，都是1
        vendor='爱立信'                        #厂家
        gnodebid = gNBId if out[NRCell]['nCI']=='<empty>' else str(int(out[NRCell]['nCI'])//4096)              #所属GNODEB ID
        gci=gnodebid+'+'+out[NRCell]['cellLocalId']                        #对象编号
        cellname=out[NRCell]['nRCellDUId'].strip('"')                        #小区名
        logger.info('NR小区名：'+cellname)
        isp='联通'                        #承建运营商
        #组网类型 即部署模式
        #条件1：exist GNBCUCPFunction.EndpointResource.LocalSctpEndpoint MO that, LocalSctpEndpoint.interfaceUsed==7 (X2)
        #条件2：exist GNBCUCPFunction.EndpointResource.LocalSctpEndpoint MO that, LocalSctpEndpoint.interfaceUsed==4 (NG)
        #条件3：找到与NRCellCU对应的NRCellDU (nCI相同), NRCellDU.secondaryCellOnly==false
        #MIX：条件1成立 & 条件2成立 & 条件3成立
        #SA： 条件2成立 & 条件1不成立
        #其它情况为NSA
        #爱立信贾工说他们都是SA
        nettype='SA'                        
        cellid=out[NRCell]['cellLocalId']                        #小区号
        tac=out[NRCell]['nRTAC']                        #TAC
        share=out[NRCell].get('share','0')                        #是否共享
        Bandwidth=out[NRCell]['bSChannelBwDL']                       #带宽
        shareBandwidth=Bandwidth if share=='1' else '0'                        #NR共享带宽
        nref=out[NRCell]['ssbFrequency']                        #5G小区下行频点
        pci=out[NRCell]['nRPCI']                        #5G小区PCI
        arfcnDL=out[NRCell]['arfcnDL']                  #NR 绝对无线频率信道号下行
        band='n1' if out[NRCell]['bandListManual']=='<empty>' else 'n'+str(eval(out[NRCell]['bandListManual'])[0])             #频带
        #输出结果
        csvList.append([sdate,isalive,islock,vendor,gci,cellname,isp,nettype,gnodebid,cellid,tac,share,shareBandwidth,Bandwidth,nref,pci,arfcnDL,band])


def deal_with_tar(tarName,sdate,csvList):
    with tarfile.open(tarName,'r') as tar:
        for i in tar.getmembers()[:]:
            #logger.info(i.name)
            if i.name=='CM_GNB_12701_2_CZ_QX_nongcunnongchangguwangjifang1ERR-share_20230316010021.txt':
                deal_with_file(tar.extractfile(i),sdate,csvList)


if __name__ == '__main__':
    csvList=[['sdate','isalive','islock','vendor','gci','cellname','isp','nettype','gnodebid','cellid','tac','share','shareBandwidth','Bandwidth','nref','pci','arfcnDL','band']]
    sdate=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for tarName in glob.glob(inpath):
        logger.info(tarName)
        deal_with_tar(tarName,sdate,csvList)
    csvName=outpath2+'ericssonNrCm_'+datetime.datetime.now().strftime("%Y%m%d%H")+'.csv'
    open(csvName+'.tmp','w').write('\n'.join([','.join(i) for i in csvList]))
    os.remove(csvName) if os.path.isfile(csvName) else None
    os.rename(csvName+'.tmp',csvName)

