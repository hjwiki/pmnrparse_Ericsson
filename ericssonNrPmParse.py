#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:haojian
# File Name: ericssonNrCmParse.py
# Created Time: 2022-7-12 15:21:48
# cm文件位置：/data/esbftp/pm/5G/ERICSSON/OMC1/PM/20220712/CUuser/PM_5G_A1_20220712150000_000.TAR.GZ


import os,sys
import logging
from logging.handlers import RotatingFileHandler
import xml.etree.ElementTree as ET
import datetime
import re
import math
import tarfile
import glob
import gzip

os.chdir(sys.path[0])
#assert ('linux' in sys.platform), '该代码只能在 Linux 下执行'

#解析时延
hour_delay=2

if 'linux' in sys.platform:
    if len(sys.argv) > 1:
        ds=str(sys.argv[1])[0:8]
        hs=str(sys.argv[1])[0:10]
    else:
        ds=(datetime.datetime.now() - datetime.timedelta(hours=hour_delay)).strftime('%Y%m%d')
        hs=(datetime.datetime.now() - datetime.timedelta(hours=hour_delay)).strftime('%Y%m%d%H')
    cmpath='/data/output/cm/ericsson/5g/ericssonNrCm_*.cs*'
    cuinpath='/data/esbftp/pm/5G/ERICSSON/OMC1/PM/%s/CUuser/PM_5G_A1_%s*.TAR.GZ'%(ds,hs)
    ctinpath='/data/esbftp/pm/5G/ERICSSON/OMC1/PM/%s/CTuser/PM_5G_A1_%s*.TAR.GZ'%(ds,hs)
    outpath='/data/output/pm/ericsson/5g/'
    #outpath='./'
    logpath='../log/'
else:
    cmpath='./ericssonNrCm_*.cs*'
    inpath='./PM_5G_A1_*.TAR.GZ'
    cuinpath='./CUuser/PM_5G_A1_*.TAR.GZ'
    ctinpath='./CTuser/PM_5G_A1_*.TAR.GZ'
    outpath='D:/'
    logpath='D:/'

#handler = RotatingFileHandler('pmParse.log',maxBytes = 100*1024*1024,backupCount = 3)
handler = logging.FileHandler(logpath+'ericssonNrPmParse_'+datetime.datetime.now().strftime("%Y%m%d")+'.log')
#handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console = logging.StreamHandler()
#console.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
logger.addHandler(handler)
if 'linux' not in sys.platform:
    logger.addHandler(console)



def deal_with_kpi(cellId,pm,starttime,interval):
    provice='河北'        #省份
    sdate=starttime        #分析时间
    eci=cellId        #,"对象编号"
    cellname=pm['cellname']        #,"对象名称"
    freq=pm['band']        #,"频段"
    bandwidth=pm['Bandwidth']        #,"带宽"
    vendor='ERICSSON'        #,"厂商名称"
    rrc_req=pm['pmRrcConnEstabAtt']        #,"RRC建立请求次数(次)"
    rrc_suc=pm['pmRrcConnEstabSucc']        #,"RRC建立成功次数(次)"
    rrc_congest=''        #,"RRC连接建立拥塞次数(次)"
    rrc_suc_ratio=0 if pm['pmRrcConnEstabAtt']==0 else pm['pmRrcConnEstabSucc']/pm['pmRrcConnEstabAtt']        #,"RRC建立成功率(%)" pmRrcConnEstabSucc/pmRrcConnEstabAtt*100%
    ng_suc_ratio=0 if pm['pmNgSigConnEstabAtt']==0 else pm['pmNgSigConnEstabSucc']/pm['pmNgSigConnEstabAtt']        #,"NG接口信令连接建立成功率"  pmNgSigConnEstabSucc/pmNgSigConnEstabAtt*100%
    ng_suc=pm['pmNgSigConnEstabSucc']        #,"NG接口信令连接建立成功次数"
    ng_req=pm['pmNgSigConnEstabAtt']        #,"NG接口信令连接建立请求次数"
    '''
    无线接入成功率 定义为以下三个成功率的乘积
    RRC建立成功率=pmRrcConnEstabSucc/pmRrcConnEstabAtt*100%
    NG建立成功率=pmNgSigConnEstabSucc/pmNgSigConnEstabAtt*100%
    初始QOS flow建立成功率=sum(pmDrbEstabSucc5qi-pmDrbEstabSuccAdded5qi)/sum(pmDrbEstabAtt5qi-pmDrbEstabAttAdded5qi)*100%
    '''
    radio_suc_ratio=0 if pm['pmRrcConnEstabAtt']==0 or pm['pmNgSigConnEstabAtt']==0 or pm['pmDrbEstabAtt5qi']-pm['pmDrbEstabAttAdded5qi']==0 else (pm['pmRrcConnEstabSucc']/pm['pmRrcConnEstabAtt'])*(pm['pmNgSigConnEstabSucc']/pm['pmNgSigConnEstabAtt'])*((pm['pmDrbEstabSucc5qi']-pm['pmDrbEstabSuccAdded5qi'])/(pm['pmDrbEstabAtt5qi']-pm['pmDrbEstabAttAdded5qi']))        #,"无线接入成功率"
    ng_suc_ratio_2=0 if pm['pmNgSigConnEstabAtt']==0 else pm['pmNgSigConnEstabSucc']/pm['pmNgSigConnEstabAtt']        #,"NG接口信令连接建立成功率" pmNgSigConnEstabSucc/pmNgSigConnEstabAtt*100%
    ng_suc_2=pm['pmNgSigConnEstabSucc']        #,"NG接口信令连接建立成功次数"
    ng_req_2=pm['pmNgSigConnEstabAtt']        #,"NG接口信令连接建立请求次数"
    qosflow_suc_ratio=0 if pm['pmDrbEstabAtt5qi']==0 else pm['pmDrbEstabSucc5qi']/pm['pmDrbEstabAtt5qi']        #,"QoSFlow建立成功率"  sum(pmDrbEstabSucc5qi)/sum(pmDrbEstabAtt5qi)*100%
    qosflow_req=pm['pmDrbEstabAtt5qi']        #,"QoSFlow建立请求数"
    qosflow_suc=pm['pmDrbEstabSucc5qi']        #,"QoSFlow建立成功数"
    ue_context_rel_total=pm['pmUeCtxtRelAmf']+pm['pmUeCtxtRelGnb']        #,"UE上下文释放总次数"  pmUeCtxtRelAmf+pmUeCtxtRelGnb
    ue_context_rel_abnormal=pm['pmUeCtxtRelAmfAbnormal']+pm['pmUeCtxtRelGnbAbnormal']        #,"UE上下文异常释放次数"
    ue_context_drop_ratio=0 if pm['pmUeCtxtRelAmf']+pm['pmUeCtxtRelGnb']==0 else (pm['pmUeCtxtRelAmfAbnormal']+pm['pmUeCtxtRelGnbAbnormal'])/(pm['pmUeCtxtRelAmf']+pm['pmUeCtxtRelGnb'])        #,"UE上下文掉线率"  (pmUeCtxtRelAmfAbnormal+pmUeCtxtRelGnbAbnormal)/(pmUeCtxtRelAmf+pmUeCtxtRelGnb)
    ul_tra_mb=(pm['pmMacVolUlResUe']+pm['pmMacVolUlResUeLastSlot']+pm['pmMacVolUlResUeLate']+pm['pmMacVolUlUnresUe'])/1000000        #,"空口上行流量" (pmMacVolUlResUe+pmMacVolUlResUeLastSlot+pmMacVolUlResUeLate+pmMacVolUlUnresUe)/1000/1000
    dl_tra_mb=(pm['pmMacVolDlDrb']+pm['pmMacVolDlDrbLastSlot']+pm['pmMacVolDlDrbSingleBurst'])/1000000        #,"空口下行流量" (pmMacVolDlDrb+pmMacVolDlDrbLastSlot+pmMacVolDlDrbSingleBurst)/1000/1000
    total_tra_mb=(pm['pmMacVolUlResUe']+pm['pmMacVolUlResUeLastSlot']+pm['pmMacVolUlResUeLate']+pm['pmMacVolUlUnresUe']+pm['pmMacVolDlDrb']+pm['pmMacVolDlDrbLastSlot']+pm['pmMacVolDlDrbSingleBurst'])/1000000        #,"空口总业务量(MByte)"
    ul_speed_mbps='' if pm['pmMacTimeUlResUe']==0 else 64*pm['pmMacVolUlResUe']/(pm['pmMacTimeUlResUe']*1000)        #,"用户上行平均吞吐率"
    dl_speed_mbps='' if pm['pmMacTimeDlDrb']==0 else 64*pm['pmMacVolDlDrb']/(pm['pmMacTimeDlDrb']*1000)        #,"用户下行平均吞吐率"
    drop_duration=pm['pmCellDowntimeMan']+pm['pmCellDowntimeAuto']        #,"小区退服时长" pmCellDowntimeMan+pmCellDowntimeAuto
    cell_available_ratio=0 if interval==0 else (interval-pm['pmCellDowntimeMan']-pm['pmCellDowntimeAuto'])/interval        #,"小区可用率" (统计时长-pmCellDowntimeAuto-pmCellDowntimeMan)/ 统计时长
    save_duration_zaipin=''        #,"节能态时长-载频关断"
    save_duration_fuhao=''        #,"节能态时长-符号关断"
    save_duration_tongdao=''        #,"节能态时长-通道关断"
    txpower=''        #,"小区平均实际发射功率"  暂不支持
    max_txpower=''        #,"小区最大实际发射功率"  暂不支持
    cqi_table1_c=sum([pm['pmRadioUeRepCqi64QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank4Distr_%d'%(i)] for i in range(0,16)])        #,"CQITable1表UE上报的CQI次数"
    cqi_table2_c=sum([pm['pmRadioUeRepCqi256QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank4Distr_%d'%(i)] for i in range(0,16)])        #,"CQITable2表UE上报的CQI次数"
    cqi_table1_ge10=sum([pm['pmRadioUeRepCqi64QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank4Distr_%d'%(i)] for i in range(10,16)])        #,"4-bitCQITable表下UE上报的CQI大于等于10的次数"
    cqi_table2_ge7=sum([pm['pmRadioUeRepCqi256QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank4Distr_%d'%(i)] for i in range(7,16)])        #,"4-bitCQITable2表下UE上报的CQI大于等于7的次数"
    cqi_high_ratio='' if sum([pm['pmRadioUeRepCqi64QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank4Distr_%d'%(i)] for i in range(0,16)])+sum([pm['pmRadioUeRepCqi256QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank4Distr_%d'%(i)] for i in range(0,16)])==0 else (sum([pm['pmRadioUeRepCqi64QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank4Distr_%d'%(i)] for i in range(10,16)])+sum([pm['pmRadioUeRepCqi256QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank4Distr_%d'%(i)] for i in range(7,16)]))/(sum([pm['pmRadioUeRepCqi64QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi64QamRank4Distr_%d'%(i)] for i in range(0,16)])+sum([pm['pmRadioUeRepCqi256QamRank1Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank2Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank3Distr_%d'%(i)]+pm['pmRadioUeRepCqi256QamRank4Distr_%d'%(i)] for i in range(0,16)]))       #,"CQI优良率"
    ul_noise='' if (pm['pmRadioRecInterferencePwrDistr_0']+pm['pmRadioRecInterferencePwrDistr_1']+pm['pmRadioRecInterferencePwrDistr_2']+pm['pmRadioRecInterferencePwrDistr_3']+pm['pmRadioRecInterferencePwrDistr_4']+pm['pmRadioRecInterferencePwrDistr_5']+pm['pmRadioRecInterferencePwrDistr_6']+pm['pmRadioRecInterferencePwrDistr_7']+pm['pmRadioRecInterferencePwrDistr_8']+pm['pmRadioRecInterferencePwrDistr_9']+pm['pmRadioRecInterferencePwrDistr_10']+pm['pmRadioRecInterferencePwrDistr_11']+pm['pmRadioRecInterferencePwrDistr_12']+pm['pmRadioRecInterferencePwrDistr_13']+pm['pmRadioRecInterferencePwrDistr_14']+pm['pmRadioRecInterferencePwrDistr_15'])==0 else ((-121)*pm['pmRadioRecInterferencePwrDistr_0']+(-120.5)*pm['pmRadioRecInterferencePwrDistr_1']+(-119.5)*pm['pmRadioRecInterferencePwrDistr_2']+(-118.5)*pm['pmRadioRecInterferencePwrDistr_3']+(-117.5)*pm['pmRadioRecInterferencePwrDistr_4']+(-116.5)*pm['pmRadioRecInterferencePwrDistr_5']+(-115.5)*pm['pmRadioRecInterferencePwrDistr_6']+(-114.5)*pm['pmRadioRecInterferencePwrDistr_7']+(-113.5)*pm['pmRadioRecInterferencePwrDistr_8']+(-112)*pm['pmRadioRecInterferencePwrDistr_9']+(-110)*pm['pmRadioRecInterferencePwrDistr_10']+(-106)*pm['pmRadioRecInterferencePwrDistr_11']+(-102)*pm['pmRadioRecInterferencePwrDistr_12']+(-98)*pm['pmRadioRecInterferencePwrDistr_13']+(-94)*pm['pmRadioRecInterferencePwrDistr_14']+(-92)*pm['pmRadioRecInterferencePwrDistr_15'])/(pm['pmRadioRecInterferencePwrDistr_0']+pm['pmRadioRecInterferencePwrDistr_1']+pm['pmRadioRecInterferencePwrDistr_2']+pm['pmRadioRecInterferencePwrDistr_3']+pm['pmRadioRecInterferencePwrDistr_4']+pm['pmRadioRecInterferencePwrDistr_5']+pm['pmRadioRecInterferencePwrDistr_6']+pm['pmRadioRecInterferencePwrDistr_7']+pm['pmRadioRecInterferencePwrDistr_8']+pm['pmRadioRecInterferencePwrDistr_9']+pm['pmRadioRecInterferencePwrDistr_10']+pm['pmRadioRecInterferencePwrDistr_11']+pm['pmRadioRecInterferencePwrDistr_12']+pm['pmRadioRecInterferencePwrDistr_13']+pm['pmRadioRecInterferencePwrDistr_14']+pm['pmRadioRecInterferencePwrDistr_15'])        #,"小区上行每PRB平均干扰电平"
    ul_pdcp_package_total=pm['pmPdcpPktUlQos']        #,"上行PDCP层用户面包总数"
    ul_pdcp_package_drop=pm['pmPdcpPktUlLossQos']        #,"上行PDCP层用户面丢包数"
    ul_pdcp_package_drop_ratio=0 if pm['pmPdcpPktUlQos']==0 else pm['pmPdcpPktUlLossQos']/pm['pmPdcpPktUlQos']        #,"上行PDCP层用户面丢包率"
    dl_pdcp_package_total=pm['pmPdcpPktDlQos']        #,"下行PDCP层用户面包总数"
    dl_pdcp_package_discard=pm['pmPdcpPktDlDiscQos']       #,"下行PDCP层用户面弃包数"
    dl_pdcp_package_discard_ratio=0 if pm['pmPdcpPktDlQos']==0 else pm['pmPdcpPktDlDiscQos']/pm['pmPdcpPktDlQos']        #,"下行PDCP层用户面弃包率"
    dl_radio_resource_utilization=0 if pm['pmMacRBSymAvailUl']==0 else sum([pm['pmMacRBSymUsedPdschMimoLayerDistr_%d'%(i)]*(i+1) for i in range(16)])/(pm['pmMacRBSymAvailUl']*16)        #,"小区下行无线资源利用率"
    ul_radio_resource_utilization=0 if pm['pmMacRBSymAvailUl']==0 else sum([pm['pmMacRBSymUsedPuschMimoLayerDistr_%d'%(i)]*(i+1) for i in range(8)])/(pm['pmMacRBSymAvailUl']*8)        #,"小区上行无线资源利用率"
    dl_rlc_user_panle_trans_duration=pm['pmMacTimeDlDrb']/8        #,"下行RLC层用户面数据发送总时长（不含最后一个slot）"
    ul_prb_used='' if interval==0 else (pm['pmMacRBSymUsedPuschTypeA']+pm['pmMacRBSymAvailPucch'])/(interval*100*pm['symbolUl'])        #,"小区上行PRB占用总数"
    ul_prb_available='' if interval==0 else (pm['pmMacRBSymAvailUl'])/(interval*100*pm['symbolUl'])        #,"小区上行PRB可用总数"
    ul_prb_utilization=0 if pm['pmMacRBSymAvailUl']==0 else (pm['pmMacRBSymUsedPuschTypeA']+pm['pmMacRBSymAvailPucch'])/pm['pmMacRBSymAvailUl']        #,"小区上行PRB平均占用率"
    dl_prb_used='' if interval==0 else (pm['pmMacRBSymUsedPdschTypeA']+pm['pmMacRBSymUsedPdcchTypeA']+pm['pmMacRBSymCsiRs'])/(interval*100*pm['symbolDl'])        #,"小区下行PRB占用总数"
    dl_prb_available='' if interval==0 else pm['pmMacRBSymAvailDl']/(interval*100*pm['symbolDl'])        #,"小区下行PRB可用总数"
    dl_prb_utilization=0 if pm['pmMacRBSymAvailDl']==0 else (pm['pmMacRBSymUsedPdschTypeA']+pm['pmMacRBSymUsedPdcchTypeA']+pm['pmMacRBSymCsiRs'])/pm['pmMacRBSymAvailDl']        #,"小区下行PRB平均占用率"
    ul_pdcp_user_panle_tra=pm['pmPdcpVolUlQos']        #,"上行PDCP层用户面流量"
    dl_pdcp_user_panle_tra=pm['pmPdcpVolDlQos']        #,"下行PDCP层用户面流量"
    ul_rl_user_panle_tra=(pm['pmMacVolUlResUe']+pm['pmMacVolUlResUeLastSlot']+pm['pmMacVolUlResUeLate']+pm['pmMacVolUlUnresUe'])/1000000        #,"上行RLC层用户面流量"
    dl_rl_user_panle_tra=(pm['pmMacVolDlDrb']+pm['pmMacVolDlDrbLastSlot']+pm['pmMacVolDlDrbSingleBurst'])/1000000        #,"下行RLC层用户面流量"
    rrc_max=pm['pmRrcConnLevelMaxSa']        #,"RRC连接最大用户数"
    ul_pusch_prb_utilization='' if pm['pmMacRBSymAvailUl']==0 else pm['pmMacRBSymUsedPuschTypeA']/pm['pmMacRBSymAvailUl']        #,"上行PUSCH信道PRB平均利用率"
    dl_pdsch_prb_utilization='' if pm['pmMacRBSymAvailDl']==0 else pm['pmMacRBSymUsedPdschTypeA']/pm['pmMacRBSymAvailDl']        #,"下行PDSCH信道PRB平均利用率"
    rrc_avg='' if pm['pmRrcConnLevelSamp']==0 else pm['pmRrcConnLevelSumSa']/pm['pmRrcConnLevelSamp']        #,"用户数均值"
    user_max=pm['pmRrcConnLevelMaxSa']        #,"最大用户数"
    qosflow_init_req=pm['pmDrbEstabAtt5qi']-pm['pmDrbEstabAttAdded5qi']        #初始QoS Flow建立请求数
    qosflow_init_suc=pm['pmDrbEstabSucc5qi']-pm['pmDrbEstabSuccAdded5qi']        #初始QoS Flow建立成功数
    qosflow_init_suc_ratio='' if pm['pmDrbEstabAtt5qi']-pm['pmDrbEstabAttAdded5qi']==0 else  (pm['pmDrbEstabSucc5qi']-pm['pmDrbEstabSuccAdded5qi'])/(pm['pmDrbEstabAtt5qi']-pm['pmDrbEstabAttAdded5qi'])        #初始QoS Flow建立成功率
    total_duration=interval        #小区统计时长(s)
    NbrRbUl='' if interval==0 else (pm['pmMacRBSymUsedPuschTypeA']+pm['pmMacRBSymAvailPucch'])/(interval*100*pm['symbolUl'])        #上行占用PRB个数的总和
    ConfigLayerUl=''        #小区上行配置层数 取基站参数：NRCellDU.ulMaxMuMimoLayers
    NbrRbDl='' if interval==0 else (pm['pmMacRBSymUsedPdschTypeA']+pm['pmMacRBSymUsedPdcchTypeA']+pm['pmMacRBSymCsiRs'])/(interval*100*pm['symbolDl'])        #下行占用PRB个数的总和
    ConfigLayerDl=''        #小区下行配置层数 取基站参数：NRCellDU.dlMaxMuMimoLayers
    pusch_prb_used='' if interval==0 else (pm['pmMacRBSymUsedPuschTypeA'])/(interval*100*pm['symbolUl'])        #上行PUSCH PRB占用总数
    pdsch_prb_used='' if interval==0 else (pm['pmMacRBSymUsedPdschTypeA'])/(interval*100*pm['symbolDl'])        #下行PDSCH PRB占用总数
    GENBID=pm['gnodebid']        #基站ID
    CI=pm['cellid']        #CI
    GNB_WIRELESS_DROP_RATIO=0 if pm['pmUeCtxtRelAmf']+pm['pmUeCtxtRelGnb']==0 else (pm['pmUeCtxtRelAmfAbnormal']+pm['pmUeCtxtRelGnbAbnormal'])/(pm['pmUeCtxtRelAmf']+pm['pmUeCtxtRelGnb'])        #5G无线掉线率(%)
    GNB_SW_SUCC_RATIO='' if pm['pmHoExeAttOutIntraGnb']+pm['pmHoPrepAttOutInterGnb']==0 else (pm['pmHoExeSuccOutIntraGnb']+pm['pmHoExeSuccOutInterGnb'])/(pm['pmHoExeAttOutIntraGnb']+pm['pmHoPrepAttOutInterGnb'])        #5G切换成功率(%)
    KPI_PDCCHCCEOCCUPANCYRATE=''        #PDCCH信道CCE占用率   暂不支持
    KPI_FLOWDROPRATE_CELLLEVEL='' if pm['pmDrbRelAmf5qi']+pm['pmDrbRelGnb5qi']==0 else (pm['pmDrbRelAmfAbnormal5qi']+pm['pmDrbRelGnbAbnormal5qi'])/(pm['pmDrbRelAmf5qi']+pm['pmDrbRelGnb5qi'])        #Flow掉线率（小区级）
    KPI_RRCCONNREESTABRATE='' if pm['pmRrcConnEstabSucc']+pm['pmRrcConnEstabAttReatt']==0 else (pm['pmRrcConnEstabAttReatt'])/(pm['pmRrcConnEstabSucc']+pm['pmRrcConnEstabAttReatt'])        #RRC连接重建比率  缺少pmRrcConnReestAtt
    KPI_HOSUCCOUTINTERGNBRATE_NG='' if pm['pmHoPrepAttOutNg']==0 else pm['pmHoExeSuccOutNg']/pm['pmHoPrepAttOutNg']       #gNB间NG切换成功率
    KPI_HOSUCCOUTINTERGNBRATE_XN=''        #gNB间Xn切换成功率 暂不支持
    KPI_HOSUCCOUTINTERGNBRATE='' if pm['pmHoPrepAttOutInterGnb']==0 else pm['pmHoExeSuccOutInterGnb']/pm['pmHoPrepAttOutInterGnb']        #gNB间切换成功率
    KPI_HOSUCCOUTINTRAGNBRATE='' if pm['pmHoExeAttOutIntraGnb']==0 else pm['pmHoExeSuccOutIntraGnb']/pm['pmHoExeAttOutIntraGnb']        #gNB内切换成功率
    KPI_HOSUCCOUTRATE_INTRAFREQ='' if pm['pmHoExeAttOutIntraFreq']==0 else pm['pmHoExeSuccOutIntraFreq']/pm['pmHoExeAttOutIntraFreq']        #同频切换执行成功率
    KPI_HOSUCCOUTRATE_INTERFREQ='' if pm['pmHoExeAttOutInterFreq']==0 else pm['pmHoExeSuccOutInterFreq']/pm['pmHoExeAttOutInterFreq']        #异频切换执行成功率
    KPI_RLCNBRPKTLOSSRATEDL=''        #小区RLC层下行丢包率  暂不支持
    KPI_MACBLERUL='' if pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']==0 else pm['pmMacHarqUlFail']/(pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])         #MAC层上行误块率
    KPI_MACBLERDL='' if pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlNack256QamInit']+pm['pmMacHarqDlDtx256QamInit']==0 else pm['pmMacHarqDlFail']/(pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlNack256QamInit']+pm['pmMacHarqDlDtx256QamInit'])         #MAC层下行误块率
    KPI_HARQRETRANSRATEUL='' if pm['pmMacHarqUlAckQpsk']+pm['pmMacHarqUlNackQpsk']+pm['pmMacHarqUlDtxQpsk']+pm['pmMacHarqUlAck16Qam']+pm['pmMacHarqUlNack16Qam']+pm['pmMacHarqUlDtx16Qam']+pm['pmMacHarqUlAck64Qam']+pm['pmMacHarqUlNack64Qam']+pm['pmMacHarqUlDtx64Qam']+pm['pmMacHarqUlAck256Qam']+pm['pmMacHarqUlNack256Qam']+pm['pmMacHarqUlDtx256Qam']==0 else   (pm['pmMacHarqUlNackQpsk']+pm['pmMacHarqUlNack16Qam']+pm['pmMacHarqUlNack64Qam']+pm['pmMacHarqUlNack256Qam'])/(pm['pmMacHarqUlAckQpsk']+pm['pmMacHarqUlNackQpsk']+pm['pmMacHarqUlDtxQpsk']+pm['pmMacHarqUlAck16Qam']+pm['pmMacHarqUlNack16Qam']+pm['pmMacHarqUlDtx16Qam']+pm['pmMacHarqUlAck64Qam']+pm['pmMacHarqUlNack64Qam']+pm['pmMacHarqUlDtx64Qam']+pm['pmMacHarqUlAck256Qam']+pm['pmMacHarqUlNack256Qam']+pm['pmMacHarqUlDtx256Qam'])      #上行HARQ重传比率
    KPI_HARQRETRANSRATEDL='' if pm['pmMacHarqDlNackQpsk']+pm['pmMacHarqDlNackQpsk']+pm['pmMacHarqDlDtxQpsk']+pm['pmMacHarqDlAck16Qam']+pm['pmMacHarqDlNack16Qam']+pm['pmMacHarqDlDtx16Qam']+pm['pmMacHarqDlAck64Qam']+pm['pmMacHarqDlNack64Qam']+pm['pmMacHarqDlDtx64Qam']+pm['pmMacHarqDlAck256Qam']+pm['pmMacHarqDlNack256Qam']+pm['pmMacHarqDlDtx256Qam']==0 else   (pm['pmMacHarqDlNackQpsk']+pm['pmMacHarqDlNack16Qam']+pm['pmMacHarqDlNack64Qam']+pm['pmMacHarqDlNack256Qam'])/(pm['pmMacHarqDlAckQpsk']+pm['pmMacHarqDlNackQpsk']+pm['pmMacHarqDlDtxQpsk']+pm['pmMacHarqDlAck16Qam']+pm['pmMacHarqDlNack16Qam']+pm['pmMacHarqDlDtx16Qam']+pm['pmMacHarqDlAck64Qam']+pm['pmMacHarqDlNack64Qam']+pm['pmMacHarqDlDtx64Qam']+pm['pmMacHarqDlAck256Qam']+pm['pmMacHarqDlNack256Qam']+pm['pmMacHarqDlDtx256Qam'])        #下行HARQ重传比率
    KPI_RANK2PERCENTDL='' if pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3']==0 else  pm['pmRadioUeRepRankDistr_1']/(pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3'])        #下行双流占比
    KPI_RANK3PERCENTDL='' if pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3']==0 else  pm['pmRadioUeRepRankDistr_2']/(pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3'])       #下行3流占比
    KPI_RANK4PERCENTDL='' if pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3']==0 else  pm['pmRadioUeRepRankDistr_3']/(pm['pmRadioUeRepRankDistr_0']+pm['pmRadioUeRepRankDistr_1']+pm['pmRadioUeRepRankDistr_2']+pm['pmRadioUeRepRankDistr_3'])        #下行4流占比
    KPI_QPSKPERCENTUL='' if pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']==0 else  (pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit'])/(pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])        #上行QPSK编码比例
    KPI_16QAMPERCENTUL='' if pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']==0 else  (pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit'])/(pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])        #上行16QAM编码比例
    KPI_64QAMPERCENTUL='' if pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']==0 else  (pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit'])/(pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])        #上行64QAM编码比例
    KPI_256QAMPERCENTUL='' if pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']==0 else  (pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])/(pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit'])        #上行256QAM编码比例
    KPI_QPSKPERCENTDL='' if pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit']==0 else  (pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit'])/(pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit'])        #下行QPSK编码比例
    KPI_16QAMPERCENTDL='' if pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit']==0 else  (pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit'])/(pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit'])        #下行16QAM编码比例
    KPI_64QAMPERCENTDL='' if pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit']==0 else  (pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit'])/(pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit'])        #下行64QAM编码比例
    KPI_256QAMPERCENTDL='' if pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit']==0 else  (pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit'])/(pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit'])        #下行256QAM编码比例
    KPI_AVGTHROUPERPRBUL=''        #上行每PRB平均吞吐量
    KPI_AVGTHROUPERPRBDL=''        #下行每PRB平均吞吐量
    KPI_AverageLayersUl='' if sum([pm['pmMacRBSymUsedPuschMimoLayerDistr_%d'%i] for i in range(1,8)])==0 else sum(pm['pmMacRBSymUsedPuschMimoLayerDistr_%d'%i]*(i+1) for i in range(1,8))/sum([pm['pmMacRBSymUsedPuschMimoLayerDistr_%d'%i] for i in range(1,8)])        #上行MIMO平均配对层数
    KPI_AverageLayersDl='' if sum([pm['pmMacRBSymUsedPdschMimoLayerDistr_%d'%i] for i in range(1,16)])==0 else sum(pm['pmMacRBSymUsedPdschMimoLayerDistr_%d'%i]*(i+1) for i in range(1,16))/sum([pm['pmMacRBSymUsedPdschMimoLayerDistr_%d'%i] for i in range(1,16)])        #下行MIMO平均配对层数
    KPI_MUPairPrbRateUl='' if (pm['pmMacRBSymUsedPuschTypeA']+pm['pmMacRBSymUsedPuschTypeB'])==0 else sum([pm['pmMacRBSymUsedPuschMimoUserDistr_%d'%i] for i in range(1,8)])/(pm['pmMacRBSymUsedPuschTypeA']+pm['pmMacRBSymUsedPuschTypeB'])       #上行MIMO配对PRB占比
    KPI_MUPairPrbRateDl='' if pm['pmMacRBSymUsedPdschTypeA']==0 else sum([pm['pmMacRBSymUsedPdschMimoUserDistr_%d'%i] for i in range(1,16)])/pm['pmMacRBSymUsedPdschTypeA']        #下行MIMO配对PRB占比
    CONTEXT_AttInitalSetup=pm['pmUeCtxtEstabAtt']        #初始上下文建立请求次数
    CONTEXT_SuccInitalSetup=pm['pmUeCtxtEstabSucc']        #初始上下文建立成功次数
    CONTEXT_FailInitalSetup=pm['pmUeCtxtEstabAtt']-pm['pmUeCtxtEstabSucc']        #初始上下文建立失败次数
    CONTEXT_AttRelgNB=pm['pmUeCtxtRelGnb']        #gNB请求释放上下文数
    CONTEXT_AttRelgNB_Normal=pm['pmUeCtxtRelGnb']-pm['pmUeCtxtRelGnbAbnormal']        #正常的gNB请求释放上下文数
    CONTEXT_NbrLeft=''        #遗留上下文个数   暂不支持
    HO_SuccExecInc=''        #切换入成功次数  暂不支持
    RRC_SuccConnReestab_NonSrccell=''   #pm['pmRrcConnReestSucc']        #RRC连接重建成功次数(非源侧小区)    找不到
    HO_SuccOutInterCuNG=pm['pmHoExeSuccOutNg']        #gNB间NG切换出成功次数
    HO_SuccOutInterCuXn=''        #gNB间Xn切换出成功次数  暂不支持
    HO_SuccOutIntraCUInterDU=''        #CU内DU间切换出执行成功次数   暂不支持
    HO_SuccOutIntraDU=''        #CU内DU内切换出成功次数  暂不支持
    HO_AttOutInterCuNG=pm['pmHoPrepAttOutNg']        #gNB间NG切换出准备请求次数
    HO_AttOutInterCuXn=''        #gNB间Xn切换出准备请求次数  暂不支持
    HO_AttOutIntraCUInterDU=''        #CU内DU间切换出执行请求次数  暂不支持
    HO_AttOutCUIntraDU=''        #CU内DU内切换出执行请求次数  暂不支持
    RRU_PuschPrbAssn='' if interval==0 else (pm['pmMacRBSymUsedPuschTypeA'])/(interval*100*pm['symbolUl'])        #上行PUSCH PRB占用数
    RRU_PuschPrbTot='' if interval==0 else (pm['pmMacRBSymAvailUl']-pm['pmMacRBSymAvailPucch']-pm['pmMacRBSymAvailRach'])/(interval*100*pm['symbolUl'])        #上行PUSCH PRB可用数
    RRU_PdschPrbAssn='' if interval==0 else (pm['pmMacRBSymUsedPdschTypeA'])/(interval*100*pm['symbolDl'])        #下行PDSCH PRB占用数
    RRU_PdcchCceUtil=''        #PDCCH信道CCE占用个数  暂不支持
    RRU_PdcchCceAvail=''        #PDCCH信道CCE可用个数  暂不支持
    Flow_NbrReqRelGnb=pm['pmDrbRelGnb5qi']        #gNB请求释放的Flow数  
    Flow_NbrReqRelGnb_Normal=pm['pmDrbRelGnb5qi']-pm['pmDrbRelGnbAbnormal5qi']        #正常的gNB请求释放的Flow数
    Flow_HoAdmitFail=''        #切出接纳失败的Flow数  暂不支持
    Flow_NbrLeft=''        #遗留Flow个数  暂不支持
    Flow_NbrHoInc=''        #切换入Flow数  暂不支持
    RRC_AttConnReestab=pm['pmRrcConnEstabAttReatt']    #pm['pmRrcConnReestAtt']        #RRC连接重建请求次数  pmRrcConnReestAtt没有
    HO_SuccOutIntraFreq=pm['pmHoExeSuccOutIntraFreq']        #同频切换出成功次数
    HO_AttOutExecIntraFreq=pm['pmHoExeAttOutIntraFreq']        #同频切换出执行请求次数
    HO_SuccOutInterFreq=pm['pmHoExeSuccOutInterFreq']        #异频切换出成功次数
    HO_AttOutExecInterFreq=pm['pmHoExeAttOutInterFreq']        #异频切换出执行请求次数
    RLC_NbrPktLossDl=''        #小区下行RLC SDU丢包数  暂不支持
    RLC_NbrPktDl=''        #小区下行RLC SDU发送包数  暂不支持
    MAC_NbrResErrTbUl=pm['pmMacHarqUlFail']        #上行残留错误TB数
    MAC_NbrInitTbUl=pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']+pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']+pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']+pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']        #上行传输初始TB数
    MAC_NbrTbUl=pm['pmMacHarqUlAckQpsk']+pm['pmMacHarqUlNackQpsk']+pm['pmMacHarqUlDtxQpsk']+pm['pmMacHarqUlAck16Qam']+pm['pmMacHarqUlNack16Qam']+pm['pmMacHarqUlDtx16Qam']+pm['pmMacHarqUlAck64Qam']+pm['pmMacHarqUlNack64Qam']+pm['pmMacHarqUlDtx64Qam']+pm['pmMacHarqUlAck256Qam']+pm['pmMacHarqUlNack256Qam']+pm['pmMacHarqUlDtx256Qam']        #上行传输TB数
    MAC_NbrResErrTbDl=pm['pmMacHarqDlFail']        #下行残留错误TB数
    MAC_NbrTbDl=pm['pmMacHarqDlAckQpsk']+pm['pmMacHarqDlNackQpsk']+pm['pmMacHarqDlDtxQpsk']+pm['pmMacHarqDlAck16Qam']+pm['pmMacHarqDlNack16Qam']+pm['pmMacHarqDlDtx16Qam']+pm['pmMacHarqDlAck64Qam']+pm['pmMacHarqDlNack64Qam']+pm['pmMacHarqDlDtx64Qam']+pm['pmMacHarqDlAck256Qam']+pm['pmMacHarqDlNack256Qam']+pm['pmMacHarqDlDtx256Qam']        #下行传输TB数
    MAC_NbrInitTbDl=pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']+pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']+pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']+pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlNack256QamInit']+pm['pmMacHarqDlDtx256QamInit']        #下行传输初始TB数
    MAC_NbrTbDl_Rank2=''        #双流下行传输TB数  暂不支持
    MAC_NbrTbDl_Rank3=''        #3流下行传输TB数  暂不支持
    MAC_NbrTbDl_Rank4=''        #4流下行传输TB数  暂不支持
    MAC_NbrInitTbUl_Qpsk=pm['pmMacHarqUlAckQpskInit']+pm['pmMacHarqUlNackQpskInit']+pm['pmMacHarqUlDtxQpskInit']        #QPSK模式上行传输初始TB数
    MAC_NbrInitTbUl_16Qam=pm['pmMacHarqUlAck16QamInit']+pm['pmMacHarqUlNack16QamInit']+pm['pmMacHarqUlDtx16QamInit']        #16QAM模式上行传输初始TB数
    MAC_NbrInitTbUl_64Qam=pm['pmMacHarqUlAck64QamInit']+pm['pmMacHarqUlNack64QamInit']+pm['pmMacHarqUlDtx64QamInit']        #64QAM模式上行传输初始TB数
    MAC_NbrInitTbUl_256Qam=pm['pmMacHarqUlAck256QamInit']+pm['pmMacHarqUlDtx256QamInit']+pm['pmMacHarqUlNack256QamInit']        #256QAM模式上行传输初始TB数
    MAC_NbrInitTbDl_Qpsk=pm['pmMacHarqDlAckQpskInit']+pm['pmMacHarqDlNackQpskInit']+pm['pmMacHarqDlDtxQpskInit']        #QPSK模式下行传输初始TB数
    MAC_NbrInitTbDl_16Qam=pm['pmMacHarqDlAck16QamInit']+pm['pmMacHarqDlNack16QamInit']+pm['pmMacHarqDlDtx16QamInit']        #16QAM模式下行传输初始TB数
    MAC_NbrInitTbDl_64Qam=pm['pmMacHarqDlAck64QamInit']+pm['pmMacHarqDlNack64QamInit']+pm['pmMacHarqDlDtx64QamInit']        #64QAM模式下行传输初始TB数
    MAC_NbrInitTbDl_256Qam=pm['pmMacHarqDlAck256QamInit']+pm['pmMacHarqDlDtx256QamInit']+pm['pmMacHarqDlNack256QamInit']        #256QAM模式下行传输初始TB数
    RRU_DtchPrbAssnUl='' if interval==0 else (pm['pmMacRBSymUsedPuschTypeA'])/(interval*100*pm['symbolUl'])        #上行业务信道占用PRB数
    RRU_DtchPrbAssnDl='' if interval==0 else (pm['pmMacRBSymUsedPdschTypeA'])/(interval*100*pm['symbolDl'])        #下行业务信道占用PRB数
    RRU_PdschPrbTot='' if interval==0 else (pm['pmMacRBSymAvailDl']-pm['pmMacRBSymCsiRs']-pm['pmMacRBSymUsedPdschTypeABroadcasting'])/(interval*100*pm['symbolDl'])        #下行PDSCH PRB可用数，分子少减了PDCCH PRB可用总数！！！！！！！！！！！！！！！需要CM依赖
    MAC_CpOctUl=''        #小区MAC层传输成功的上行流量  暂不支持
    MAC_CpOctDl=''        #小区MAC层传输成功的下行流量  暂不支持
    PHY_ULMaxNL_PRB='' if pm['pmRadioRecInterferencePwrPRBMax_num']==0 else max([pm['pmRadioRecInterferencePwrPRBMax_%d'%i] for i in range(1,pm['pmRadioRecInterferencePwrPRBMax_num']+1)])        #小区RB上行最大干扰电平
    RRC_RedirectToLTE=pm['pmRwrEutranUeSuccNrCoverage']+pm['pmRwrEutranUeSuccEpsfb']+pm['pmRwrEutranUeSuccEpsfbEm']        #RRC 重定向到LTE次数
    RRC_RedirectToLTE_EpsFB=pm['pmRwrEutranUeSuccEpsfb']+pm['pmRwrEutranUeSuccEpsfbEm']        #EPS fallback RRC 重定向到LTE次数
    RRC_SAnNsaConnUserMean='' if pm['pmRrcConnLevelSamp']==0 else pm['pmRrcConnLevelSumSa']/pm['pmRrcConnLevelSamp']        #小区平均用户数
    HoPrepAttOutEutran=pm['pmHoPrepAttOutEutranNrCoverage']        #NR切换LTE请求次数（数据触发）
    HoExeSuccOutEutran=pm['pmHoExeSuccOutEutranNrCoverage']        #NR切换LTE成功次数（数据触发）
    RwrEutranUeSucc=pm['pmRwrEutranUeSuccNrCoverage']        #5G重定向到4G的总次数（数据触发）
    #2022-8-22添加
    a_isp='联通'             #承建运营商    联通
    a_ul_speed_fz=64*pm['pmMacVolUlResUe']             #用户上行平均吞吐率_分子    64*pmMacVolUlResUe
    a_ul_speed_fm=pm['pmMacTimeUlResUe']*1000             #用户上行平均吞吐率_分母    pmMacTimeUlResUe*1000
    a_dl_speed_fz=64*pm['pmMacVolDlDrb']             #用户下行平均吞吐率_分子    64*pmMacVolDlDrb
    a_dl_speed_fm=pm['pmMacTimeDlDrb']*1000             #用户下行平均吞吐率_分母    pmMacTimeDlDrb*1000
    a_PDCP_SDU_VOL_UL_plmn1=(pm['pmMacVolUlResUePlmn46001']+pm['pmMacVolUlResUeLastSlotPlmn46001']+pm['pmMacVolUlResUeLatePlmn46001']+pm['pmMacVolUlUnresUePlmn46001'])/1000000                       #空口上行业务流量（PDCP）(联通46001)(MByte)    (pmMacVolUlResUePlmn46001+pmMacVolUlResUeLastSlotPlmn46001+pmMacVolUlResUeLatePlmn46001+pmMacVolUlUnresUePlmn46001)/1000/1000
    a_PDCP_SDU_VOL_DL_plmn1=(pm['pmMacVolDlDrbPlmn46001']+pm['pmMacVolDlDrbLastSlotPlmn46001']+pm['pmMacVolDlDrbSingleBurstPlmn46001'])/1000000                       #空口下行业务流量（PDCP）(联通46001)(MByte)    (pmMacVolDlDrbPlmn46001+pmMacVolDlDrbLastSlotPlmn46001+pmMacVolDlDrbSingleBurstPlmn46001)/1000/1000
    a_rrc_avg_plmn1=pm['pmRrcConnLevelSumSaPlmn46001']                       #RRC连接平均数(联通46001)    pmRrcConnLevelSumSaPlmn46001
    a_PDCP_SDU_VOL_UL_plmn2=(pm['pmMacVolUlResUePlmn46011']+pm['pmMacVolUlResUeLastSlotPlmn46011']+pm['pmMacVolUlResUeLatePlmn46011']+pm['pmMacVolUlUnresUePlmn46011'])/1000000                       #空口上行业务流量（PDCP）(电信46011)(MByte)    (pmMacVolUlResUePlmn46011+pmMacVolUlResUeLastSlotPlmn46011+pmMacVolUlResUeLatePlmn46011+pmMacVolUlUnresUePlmn46011)/1000/1000
    a_PDCP_SDU_VOL_DL_plmn2=(pm['pmMacVolDlDrbPlmn46011']+pm['pmMacVolDlDrbLastSlotPlmn46011']+pm['pmMacVolDlDrbSingleBurstPlmn46011'])/1000000                       #空口下行业务流量（PDCP）(电信46011)(MByte)    (pmMacVolDlDrbPlmn46011+pmMacVolDlDrbLastSlotPlmn46011+pmMacVolDlDrbSingleBurstPlmn46011)/1000/1000
    a_rrc_avg_plmn2=pm['pmRrcConnLevelSumSaPlmn46011']                       #RRC连接平均数(电信46011)    pmRrcConnLevelSumSaPlmn46011
    a_kpi185=pm['pmPdcpPktUlLossQosPlmn46001_1']+pm['pmPdcpPktUlLossQosPlmn46011_1']                       #小区中5QI1的PDCP上行业务丢包数(包)
    a_kpi186=pm['pmPdcpPktUlQosPlmn46001_1']+pm['pmPdcpPktUlQosPlmn46011_1']                       #小区中5QI1的PDCP收到上行RLC层的PDU包数(包)
    a_kpi187=pm['pmPdcpPktDlQosPlmn46001_1']+pm['pmPdcpPktDlQosPlmn46011_1']                       #DU小区中5QI1的RLC层收到的下行SDU包数(包)
    a_kpi188=pm['pmDrbEstabSuccInit5qiPlmn46001_1']+pm['pmDrbEstabSuccAdded5qiPlmn46001_1']+pm['pmDrbEstabSuccInit5qiPlmn46011_1']+pm['pmDrbEstabSuccAdded5qiPlmn46011_1']                       #QosFlow建立成功次数(5QI1)
    a_kpi189=pm['pmDrbEstabAttInit5qiPlmn46001_1']+pm['pmDrbEstabAttAdded5qiPlmn46001_1']-pm['pmDrbEstabAttAddedEpsfb5qiPlmn46001_1']-pm['pmDrbEstabAttInitEpsfb5qiPlmn46001_1']+(pm['pmDrbEstabAttInit5qiPlmn46011_1']+pm['pmDrbEstabAttAdded5qiPlmn46011_1']-pm['pmDrbEstabAttAddedEpsfb5qiPlmn46011_1']-pm['pmDrbEstabAttInitEpsfb5qiPlmn46011_1'])                       #QosFlow建立请求次数(5QI1)
    a_kpi190='' if a_kpi189==0 else a_kpi188/a_kpi189                       #QosFlow建立成功率(5QI1)
    a_kpi191=pm['pmDrbRelAmfAbnormal5qi_1']+pm['pmDrbRelGnbAbnormal5qi_1']                       #VoNR掉话次数(5QI1)
    a_kpi192=pm['pmDrbRelAmf5qi_1']+pm['pmDrbRelGnb5qi_1']                       #VoNR总释放次数(5QI1)
    a_kpi193='' if a_kpi192==0 else a_kpi191/a_kpi192                       #VoNR掉话率(5QI1)
    a_kpi194=pm['pmPdcpPktUlLossQosPlmn46001_1']+pm['pmPdcpPktUlLossQosPlmn46011_1']                       #VoNR上行丢包数(5QI1)
    a_kpi195=pm['pmPdcpPktUlQosPlmn46001_1']+pm['pmPdcpPktUlQosPlmn46011_1']                       #VoNR上行总包数(5QI1)
    a_kpi196='' if a_kpi195==0 else a_kpi194/a_kpi195                       #VoNR上行丢包率(5QI1)
    a_kpi197=pm['pmPdcpPktDlDiscQosPlmn46001_1']+pm['pmPdcpPktDlDiscQosPlmn46011_1']                       #VoNR下行丢包数(5QI1)
    a_kpi198=pm['pmPdcpPktDlQosPlmn46001_1']+pm['pmPdcpPktDlQosPlmn46011_1']                       #VoNR下行总包数(5QI1)
    a_kpi199='' if a_kpi198==0 else a_kpi197/a_kpi198                       #VoNR下行丢包率(5QI1)
    a_qosflow_5qi5_req=pm['pmDrbEstabAttInit5qiPlmn46001_5']+pm['pmDrbEstabAttAdded5qiPlmn46001_5']-pm['pmDrbEstabAttAddedEpsfb5qiPlmn46001_5']-pm['pmDrbEstabAttInitEpsfb5qiPlmn46001_5']                       #QosFlow建立请求次数(5QI5)
    a_qosflow_5qi5_suc=pm['pmDrbEstabSuccInit5qiPlmn46001_5']+pm['pmDrbEstabSuccAdded5qiPlmn46001_5']                       #QosFlow建立成功次数(5QI5)
    a_qosflow_5qi5_suc_ratio='' if a_qosflow_5qi5_req==0 else a_qosflow_5qi5_suc/a_qosflow_5qi5_req                       #QosFlow建立成功率(5QI5)

    return [provice,sdate,eci,cellname,freq,bandwidth,vendor,rrc_req,rrc_suc,rrc_congest,rrc_suc_ratio,ng_suc_ratio,ng_suc,ng_req,radio_suc_ratio,ng_suc_ratio_2,ng_suc_2,ng_req_2,qosflow_suc_ratio,qosflow_req,qosflow_suc,ue_context_rel_total,ue_context_rel_abnormal,ue_context_drop_ratio,ul_tra_mb,dl_tra_mb,total_tra_mb,ul_speed_mbps,dl_speed_mbps,drop_duration,cell_available_ratio,save_duration_zaipin,save_duration_fuhao,save_duration_tongdao,txpower,max_txpower,cqi_table1_c,cqi_table2_c,cqi_table1_ge10,cqi_table2_ge7,cqi_high_ratio,ul_noise,ul_pdcp_package_total,ul_pdcp_package_drop,ul_pdcp_package_drop_ratio,dl_pdcp_package_total,dl_pdcp_package_discard,dl_pdcp_package_discard_ratio,dl_radio_resource_utilization,ul_radio_resource_utilization,dl_rlc_user_panle_trans_duration,ul_prb_used,ul_prb_available,ul_prb_utilization,dl_prb_used,dl_prb_available,dl_prb_utilization,ul_pdcp_user_panle_tra,dl_pdcp_user_panle_tra,ul_rl_user_panle_tra,dl_rl_user_panle_tra,rrc_max,ul_pusch_prb_utilization,dl_pdsch_prb_utilization,rrc_avg,user_max,qosflow_init_req,qosflow_init_suc,qosflow_init_suc_ratio,total_duration,NbrRbUl,ConfigLayerUl,NbrRbDl,ConfigLayerDl,pusch_prb_used,pdsch_prb_used,GENBID,CI,GNB_WIRELESS_DROP_RATIO,GNB_SW_SUCC_RATIO,KPI_PDCCHCCEOCCUPANCYRATE,KPI_FLOWDROPRATE_CELLLEVEL,KPI_RRCCONNREESTABRATE,KPI_HOSUCCOUTINTERGNBRATE_NG,KPI_HOSUCCOUTINTERGNBRATE_XN,KPI_HOSUCCOUTINTERGNBRATE,KPI_HOSUCCOUTINTRAGNBRATE,KPI_HOSUCCOUTRATE_INTRAFREQ,KPI_HOSUCCOUTRATE_INTERFREQ,KPI_RLCNBRPKTLOSSRATEDL,KPI_MACBLERUL,KPI_MACBLERDL,KPI_HARQRETRANSRATEUL,KPI_HARQRETRANSRATEDL,KPI_RANK2PERCENTDL,KPI_RANK3PERCENTDL,KPI_RANK4PERCENTDL,KPI_QPSKPERCENTUL,KPI_16QAMPERCENTUL,KPI_64QAMPERCENTUL,KPI_256QAMPERCENTUL,KPI_QPSKPERCENTDL,KPI_16QAMPERCENTDL,KPI_64QAMPERCENTDL,KPI_256QAMPERCENTDL,KPI_AVGTHROUPERPRBUL,KPI_AVGTHROUPERPRBDL,KPI_AverageLayersUl,KPI_AverageLayersDl,KPI_MUPairPrbRateUl,KPI_MUPairPrbRateDl,CONTEXT_AttInitalSetup,CONTEXT_SuccInitalSetup,CONTEXT_FailInitalSetup,CONTEXT_AttRelgNB,CONTEXT_AttRelgNB_Normal,CONTEXT_NbrLeft,HO_SuccExecInc,RRC_SuccConnReestab_NonSrccell,HO_SuccOutInterCuNG,HO_SuccOutInterCuXn,HO_SuccOutIntraCUInterDU,HO_SuccOutIntraDU,HO_AttOutInterCuNG,HO_AttOutInterCuXn,HO_AttOutIntraCUInterDU,HO_AttOutCUIntraDU,RRU_PuschPrbAssn,RRU_PuschPrbTot,RRU_PdschPrbAssn,RRU_PdcchCceUtil,RRU_PdcchCceAvail,Flow_NbrReqRelGnb,Flow_NbrReqRelGnb_Normal,Flow_HoAdmitFail,Flow_NbrLeft,Flow_NbrHoInc,RRC_AttConnReestab,HO_SuccOutIntraFreq,HO_AttOutExecIntraFreq,HO_SuccOutInterFreq,HO_AttOutExecInterFreq,RLC_NbrPktLossDl,RLC_NbrPktDl,MAC_NbrResErrTbUl,MAC_NbrInitTbUl,MAC_NbrTbUl,MAC_NbrResErrTbDl,MAC_NbrTbDl,MAC_NbrInitTbDl,MAC_NbrTbDl_Rank2,MAC_NbrTbDl_Rank3,MAC_NbrTbDl_Rank4,MAC_NbrInitTbUl_Qpsk,MAC_NbrInitTbUl_16Qam,MAC_NbrInitTbUl_64Qam,MAC_NbrInitTbUl_256Qam,MAC_NbrInitTbDl_Qpsk,MAC_NbrInitTbDl_16Qam,MAC_NbrInitTbDl_64Qam,MAC_NbrInitTbDl_256Qam,RRU_DtchPrbAssnUl,RRU_DtchPrbAssnDl,RRU_PdschPrbTot,MAC_CpOctUl,MAC_CpOctDl,PHY_ULMaxNL_PRB,RRC_RedirectToLTE,RRC_RedirectToLTE_EpsFB,RRC_SAnNsaConnUserMean,HoPrepAttOutEutran,HoExeSuccOutEutran,RwrEutranUeSucc,
            #2022-8-22添加
            a_isp,a_ul_speed_fz,a_ul_speed_fm,a_dl_speed_fz,a_dl_speed_fm,
            #2022-10-20添加
            a_PDCP_SDU_VOL_UL_plmn1,a_PDCP_SDU_VOL_DL_plmn1,a_rrc_avg_plmn1,a_PDCP_SDU_VOL_DL_plmn2,a_PDCP_SDU_VOL_DL_plmn2,a_rrc_avg_plmn2,
            #2023-3-15添加
            a_kpi185,a_kpi186,a_kpi187,a_kpi188,a_kpi189,a_kpi190,a_kpi191,a_kpi192,a_kpi193,a_kpi194,a_kpi195,a_kpi196,a_kpi197,a_kpi198,a_kpi199,
            #2023-4-19添加
            a_qosflow_5qi5_req,a_qosflow_5qi5_suc,a_qosflow_5qi5_suc_ratio]



def deal_with_file(xmltext,cell,csvList,counters,tarName,xmlname,ctCounter):
    outlte=dict()
    outnr=dict()
    fdn=[]
    ns={'ns1':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec',
        'ns2':'http://www.w3.org/2001/XMLSchema-instance',
        'ns3':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec'}
    root=ET.fromstring(xmltext)
    fileHeader = root.find('ns1:fileHeader',ns)
    localDn=fileHeader.find('ns1:fileSender',ns).attrib['localDn']
    elementType=fileHeader.find('ns1:fileSender',ns).attrib['elementType']
    beginTime=fileHeader.find('ns1:measCollec',ns).attrib['beginTime']
    beginTime=beginTime[0:10]+' '+beginTime[11:19]
    beginTime=(datetime.datetime.strptime(beginTime,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    measData=root.find('ns1:measData',ns)
    for measInfo in [i for i in measData.findall('ns1:measInfo',ns)]:
        if measInfo.attrib['measInfoId']=="PM=1,PmGroup=EUtranCellFDD" and measInfo.find('ns1:job',ns).attrib['jobId']=='USERDEF-LTECONTERS.Cont.Y.STATS':
            #小区级别counter
            #<measInfo measInfoId="PM=1,PmGroup=EUtranCellFDD">
            #  <job jobId="USERDEF-LTECONTERS.Cont.Y.STATS"/>
            #  <granPeriod duration="PT900S"
            #              endTime="2022-06-20T01:15:00+00:00"/>
            #  <repPeriod duration="PT900S"/>
            #  <measType p="1">pmAcBarringVideoSpecialAcDistr</measType>
            #  ...
            #  <measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDBG_DianXinXinDaLou-SF-2100MERR-share,ManagedElement=BDBG_DianXinXinDaLou-SF-2100MERR-share,ENodeBFunction=1,EUtranCellFDD=BDBG_DianXinXinDaLou-SF-2100MERF_1">
            #  <r p="1">0,0,0,0,0</r>
            #  ...
            duration=int(measInfo.find('ns1:repPeriod',ns).attrib['duration'][2:-1])
            pmList=[i.text for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measType']
            for measValue in [i for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measValue']:
                measObjLdn=measValue.attrib['measObjLdn']   #小区名节点：<measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDBG_DianXinXinDaLou-SF-2100MERR-share,ManagedElement=BDBG_DianXinXinDaLou-SF-2100MERR-share,ENodeBFunction=1,EUtranCellFDD=BDBG_DianXinXinDaLou-SF-2100MERF_1"> 
                measObjLdn=[i for i in measObjLdn.split(',') if i.startswith('EUtranCellFDD=')][0].split('=')[1]
                d_=dict(zip(pmList,[i.text for i in list(measValue)]))
                for c in pmList:
                    if ',' not in d_[c]:
                        d_[c]=int(d_[c])
                    elif c.endswith('Qci'):
                        #'pmErabEstabAttInitQci':'2,5,10,9,8'
                        d_[c]=d_[c].split(',')
                        for i in zip(d_[c][1::2],d_[c][2::2]):
                            d_[c+'_'+i[0]]= 0 if i[1]==' ' else int(i[1])
                    else:
                        #'pmMacUeThpDlDistr':'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
                        d_[c]=d_[c].split(',')
                        for inx, val in enumerate(d_[c]):
                            d_[c+'_%d'%inx]=int(val)
                if measObjLdn in outlte:
                    outlte[measObjLdn].update(d_)
                else:
                    outlte[measObjLdn]=d_
        elif (measInfo.attrib['measInfoId']=='PM=1,PmGroup=NRCellDU_GNBDU' and measInfo.find('ns1:job',ns).attrib['jobId'] in ['NBI_Counters_XML','ESANRJob','NBI_Counters_ESACUCP','PREDEF_5GRP','NBI_Counters_XML','PREDEF_5GRC','USERDEF-STATISTICAL_Counters.Cont.Y.STATS']) or (measInfo.attrib['measInfoId']=='PM=1,PmGroup=NRCellCU_GNBCUCP' and measInfo.find('ns1:job',ns).attrib['jobId'] in ['PREDEF_5GRC','NBI_Counters_XML','ESANRJob','USERDEF-STATISTICAL_Counters.Cont.Y.STATS','NBI_Counters_ESACUCP','NBI_Counters_XMLESA']):
            duration=int(measInfo.find('ns1:repPeriod',ns).attrib['duration'][2:-1])
            pmList=[i.text for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measType']
            for measValue in [i for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measValue']:
                measObjLdn=measValue.attrib['measObjLdn']       #小区名节点：<measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDGB_QuXinZhuangCun2100MERR-share,ManagedElement=BDGB_QuXinZhuangCun2100MERR-share,GNBCUCPFunction=gNBId2301827,NRCellCU=BDGB_QuXinZhuangCun2100MERR-share_2" objectUID="12701_ERICSSON_NRCellCU_2_2301827_1025">
                measObjLdn=[i for i in measObjLdn.split(',') if i.startswith('NRCellCU=') or i.startswith('NRCellDU=')][0].split('=')[1]
                d_=dict(zip(pmList,[i.text for i in list(measValue)]))
                for c in pmList:
                    if ',' not in d_[c]:
                        if '.' not in d_[c]:
                            d_[c]=int(d_[c])
                        else:
                            d_[c]=float(d_[c])
                    elif c.endswith('Qos') or c.endswith('5qi') or c.endswith('PwrPRB') or c.endswith('PwrPRBMax') or c.endswith('5qiPlmn46001') or c.endswith('QosPlmn46001'):
                        #'pmDrbEstabSucc5qi':'3,5,1,8,9,9,9'
                        d_[c]=d_[c].split(',')
                        d_[c+'_num']=int(d_[c][0])
                        for i in zip(d_[c][1::2],d_[c][2::2]):
                            d_[c+'_'+i[0]]= 0 if i[1]==' ' else eval(i[1])
                        d_[c]=sum([0 if i==' ' else eval(i) for i in d_[c][2::2]])
                    else:
                        #'pmMacUeThpDlDistr':'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
                        d_[c]=d_[c].split(',')
                        for inx, val in enumerate(d_[c]):
                            d_[c+'_%d'%inx]=int(val)
                if measObjLdn in outnr:
                    outnr[measObjLdn].update(d_)
                else:
                    outnr[measObjLdn]=d_

    #解析完成，开始运算
    for measObjLdn in outnr:
        logger.info(measObjLdn)
        if measObjLdn in cell:
            #cellId=cell[measObjLdn][4]  #,"对象编号"
            cellId='127.'+cell[measObjLdn][8]+'.'+cell[measObjLdn][9]  #,"对象编号"
            outnr[measObjLdn]['share']=cell[measObjLdn][11]   #是否共享
            outnr[measObjLdn]['cellname']=measObjLdn    #,"对象名称"
            outnr[measObjLdn]['band']=cell[measObjLdn][17]        #,"频段"
            outnr[measObjLdn]['Bandwidth']=cell[measObjLdn][13]        #,"带宽"
            outnr[measObjLdn]['gnodebid']=cell[measObjLdn][8]       #基站ID
            outnr[measObjLdn]['cellid']=cell[measObjLdn][9]     #CI
            outnr[measObjLdn]['symbolUl']={'n78':84,'n1':140}[cell[measObjLdn][17]]    #符号数 n1:2.1G FDD 140个 n78:3.5G TDD 84个
            outnr[measObjLdn]['symbolDl']={'n78':166,'n1':130}[cell[measObjLdn][17]]    #符号数 n1:2.1G FDD 130个 n78:3.5G TDD 166个
            if beginTime in ctCounter and measObjLdn in ctCounter[beginTime]:
                outnr[measObjLdn].update(ctCounter[beginTime][measObjLdn])
            try:
                kpi=deal_with_kpi(cellId,outnr[measObjLdn],beginTime,duration)
            except KeyError as e:
                logger.error(measObjLdn+'\t:\t'+str(e))
                counters.add(eval(str(e)))
                outnr[measObjLdn].update({i:0 for i in counters-set(outnr[measObjLdn])})
                kpi=deal_with_kpi(cellId,outnr[measObjLdn],beginTime,duration)
            #csvList.append([str(i) for i in kpi]+[tarName,xmlname])   #添加tarname和xmlname用于核查
            csvList.append([str(i) for i in kpi])
        else:
            logger.error('！！！！！！！！！！！缺少小区CM信息\t：\t'+measObjLdn)

def deal_with_ct_file(xmltext,ctCounter):
    outlte=dict()
    outnr=dict()
    fdn=[]
    ns={'ns1':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec',
        'ns2':'http://www.w3.org/2001/XMLSchema-instance',
        'ns3':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec'}
    root=ET.fromstring(xmltext)
    fileHeader = root.find('ns1:fileHeader',ns)
    localDn=fileHeader.find('ns1:fileSender',ns).attrib['localDn']
    elementType=fileHeader.find('ns1:fileSender',ns).attrib['elementType']
    beginTime=fileHeader.find('ns1:measCollec',ns).attrib['beginTime']
    beginTime=beginTime[0:10]+' '+beginTime[11:19]
    beginTime=(datetime.datetime.strptime(beginTime,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    measData=root.find('ns1:measData',ns)
    for measInfo in [i for i in measData.findall('ns1:measInfo',ns)]:
        if measInfo.attrib['measInfoId']=="PM=1,PmGroup=EUtranCellFDD" and measInfo.find('ns1:job',ns).attrib['jobId']=='USERDEF-LTECONTERS.Cont.Y.STATS':
            #小区级别counter
            #<measInfo measInfoId="PM=1,PmGroup=EUtranCellFDD">
            #  <job jobId="USERDEF-LTECONTERS.Cont.Y.STATS"/>
            #  <granPeriod duration="PT900S"
            #              endTime="2022-06-20T01:15:00+00:00"/>
            #  <repPeriod duration="PT900S"/>
            #  <measType p="1">pmAcBarringVideoSpecialAcDistr</measType>
            #  ...
            #  <measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDBG_DianXinXinDaLou-SF-2100MERR-share,ManagedElement=BDBG_DianXinXinDaLou-SF-2100MERR-share,ENodeBFunction=1,EUtranCellFDD=BDBG_DianXinXinDaLou-SF-2100MERF_1">
            #  <r p="1">0,0,0,0,0</r>
            #  ...
            duration=int(measInfo.find('ns1:repPeriod',ns).attrib['duration'][2:-1])
            pmList=[i.text for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measType']
            for measValue in [i for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measValue']:
                measObjLdn=measValue.attrib['measObjLdn']   #小区名节点：<measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDBG_DianXinXinDaLou-SF-2100MERR-share,ManagedElement=BDBG_DianXinXinDaLou-SF-2100MERR-share,ENodeBFunction=1,EUtranCellFDD=BDBG_DianXinXinDaLou-SF-2100MERF_1"> 
                measObjLdn=[i for i in measObjLdn.split(',') if i.startswith('EUtranCellFDD=')][0].split('=')[1]
                d_=dict(zip(pmList,[i.text for i in list(measValue)]))
                for c in pmList:
                    if ',' not in d_[c]:
                        d_[c]=int(d_[c])
                    elif c.endswith('Qci'):
                        #'pmErabEstabAttInitQci':'2,5,10,9,8'
                        d_[c]=d_[c].split(',')
                        for i in zip(d_[c][1::2],d_[c][2::2]):
                            d_[c+'_'+i[0]]= 0 if i[1]==' ' else int(i[1])
                    else:
                        #'pmMacUeThpDlDistr':'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
                        d_[c]=d_[c].split(',')
                        for inx, val in enumerate(d_[c]):
                            d_[c+'_%d'%inx]=int(val)
                if measObjLdn in outlte:
                    outlte[measObjLdn].update(d_)
                else:
                    outlte[measObjLdn]=d_
        elif (measInfo.attrib['measInfoId']=='PM=1,PmGroup=NRCellDU_GNBDU' and measInfo.find('ns1:job',ns).attrib['jobId'] in ['NBI_Counters_XML','ESANRJob','NBI_Counters_ESACUCP','PREDEF_5GRP','NBI_Counters_XML','PREDEF_5GRC','USERDEF-STATISTICAL_Counters.Cont.Y.STATS']) or (measInfo.attrib['measInfoId']=='PM=1,PmGroup=NRCellCU_GNBCUCP' and measInfo.find('ns1:job',ns).attrib['jobId'] in ['PREDEF_5GRC','NBI_Counters_XML','ESANRJob','USERDEF-STATISTICAL_Counters.Cont.Y.STATS','NBI_Counters_ESACUCP','NBI_Counters_XMLESA']):
            duration=int(measInfo.find('ns1:repPeriod',ns).attrib['duration'][2:-1])
            pmList=[i.text for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measType']
            for measValue in [i for i in list(measInfo) if i.tag=='{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measValue']:
                measObjLdn=measValue.attrib['measObjLdn']       #小区名节点：<measValue measObjLdn="SubNetwork=CUHeB_BD_MIX_2.1,MeContext=BDGB_QuXinZhuangCun2100MERR-share,ManagedElement=BDGB_QuXinZhuangCun2100MERR-share,GNBCUCPFunction=gNBId2301827,NRCellCU=BDGB_QuXinZhuangCun2100MERR-share_2" objectUID="12701_ERICSSON_NRCellCU_2_2301827_1025">
                measObjLdn=[i for i in measObjLdn.split(',') if i.startswith('NRCellCU=') or i.startswith('NRCellDU=')][0].split('=')[1]
                d_=dict(zip(pmList,[i.text for i in list(measValue)]))
                for c in pmList:
                    if ',' not in d_[c]:
                        if '.' not in d_[c]:
                            d_[c]=int(d_[c])
                        else:
                            d_[c]=float(d_[c])
                    elif c.endswith('Qos') or c.endswith('5qi') or c.endswith('PwrPRB') or c.endswith('PwrPRBMax') or c.endswith('5qiPlmn46011') or c.endswith('QosPlmn46011'):
                        #'pmDrbEstabSucc5qi':'3,5,1,8,9,9,9'
                        d_[c]=d_[c].split(',')
                        d_[c+'_num']=int(d_[c][0])
                        for i in zip(d_[c][1::2],d_[c][2::2]):
                            d_[c+'_'+i[0]]= 0 if i[1]==' ' else eval(i[1])
                        d_[c]=sum([0 if i==' ' else eval(i) for i in d_[c][2::2]])
                    else:
                        #'pmMacUeThpDlDistr':'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
                        d_[c]=d_[c].split(',')
                        for inx, val in enumerate(d_[c]):
                            d_[c+'_%d'%inx]=int(val)
                if measObjLdn in outnr:
                    outnr[measObjLdn].update(d_)
                else:
                    outnr[measObjLdn]=d_

    #解析完成，将plmn46011的指标放入ctCounter
    if beginTime not in ctCounter:
        ctCounter[beginTime]=outnr
    else:
        ctCounter[beginTime].update(outnr)

def deal_with_tar(tarName,cell,csvList,counters,ctCounter):
    with tarfile.open(tarName,'r') as tar:
        for i in tar.getmembers()[:]:
            #if i.name not in ['PM_GNB_12701_2_BDBG_PengRunMeiShuJia2Qi3-SF-2100MERR-share_20230321103000.xml']:
            #    continue
            logger.info(i.name)
            try:
                deal_with_file(tar.extractfile(i).read(),cell,csvList,counters,tarName,i.name,ctCounter)
            except ET.ParseError as e:
                logger.error('ParseError'+':'+str(e)+':'+i.name)

def deal_with_ct_tar(tarName,ctCounter):
    with tarfile.open(tarName,'r') as tar:
        for i in tar.getmembers()[:]:
            #if i.name not in ['PM_GNB_12701_2_BDBG_PengRunMeiShuJia2Qi3-SF-2100MERR-share_20230321103000.xml']:
            #    continue
            logger.info(i.name)
            try:
                deal_with_ct_file(tar.extractfile(i).read(),ctCounter)
            except ET.ParseError as e:
                logger.error('ParseError'+':'+str(e)+':'+i.name)


if __name__ == '__main__':
    csvList=[['provice','sdate','eci','cellname','freq','bandwidth','vendor','rrc_req','rrc_suc','rrc_congest','rrc_suc_ratio','ng_suc_ratio','ng_suc','ng_req','radio_suc_ratio','ng_suc_ratio_2','ng_suc_2','ng_req_2','qosflow_suc_ratio','qosflow_req','qosflow_suc','ue_context_rel_total','ue_context_rel_abnormal','ue_context_drop_ratio','ul_tra_mb','dl_tra_mb','total_tra_mb','ul_speed_mbps','dl_speed_mbps','drop_duration','cell_available_ratio','save_duration_zaipin','save_duration_fuhao','save_duration_tongdao','txpower','max_txpower','cqi_table1_c','cqi_table2_c','cqi_table1_ge10','cqi_table2_ge7','cqi_high_ratio','ul_noise','ul_pdcp_package_total','ul_pdcp_package_drop','ul_pdcp_package_drop_ratio','dl_pdcp_package_total','dl_pdcp_package_discard','dl_pdcp_package_discard_ratio','dl_radio_resource_utilization','ul_radio_resource_utilization','dl_rlc_user_panle_trans_duration','ul_prb_used','ul_prb_available','ul_prb_utilization','dl_prb_used','dl_prb_available','dl_prb_utilization','ul_pdcp_user_panle_tra','dl_pdcp_user_panle_tra','ul_rl_user_panle_tra','dl_rl_user_panle_tra','rrc_max','ul_pusch_prb_utilization','dl_pdsch_prb_utilization','rrc_avg','user_max','qosflow_init_req','qosflow_init_suc','qosflow_init_suc_ratio','total_duration','NbrRbUl','ConfigLayerUl','NbrRbDl','ConfigLayerDl','pusch_prb_used','pdsch_prb_used','GENBID','CI','GNB_WIRELESS_DROP_RATIO','GNB_SW_SUCC_RATIO','KPI_PDCCHCCEOCCUPANCYRATE','KPI_FLOWDROPRATE_CELLLEVEL','KPI_RRCCONNREESTABRATE','KPI_HOSUCCOUTINTERGNBRATE_NG','KPI_HOSUCCOUTINTERGNBRATE_XN','KPI_HOSUCCOUTINTERGNBRATE','KPI_HOSUCCOUTINTRAGNBRATE','KPI_HOSUCCOUTRATE_INTRAFREQ','KPI_HOSUCCOUTRATE_INTERFREQ','KPI_RLCNBRPKTLOSSRATEDL','KPI_MACBLERUL','KPI_MACBLERDL','KPI_HARQRETRANSRATEUL','KPI_HARQRETRANSRATEDL','KPI_RANK2PERCENTDL','KPI_RANK3PERCENTDL','KPI_RANK4PERCENTDL','KPI_QPSKPERCENTUL','KPI_16QAMPERCENTUL','KPI_64QAMPERCENTUL','KPI_256QAMPERCENTUL','KPI_QPSKPERCENTDL','KPI_16QAMPERCENTDL','KPI_64QAMPERCENTDL','KPI_256QAMPERCENTDL','KPI_AVGTHROUPERPRBUL','KPI_AVGTHROUPERPRBDL','KPI_AverageLayersUl','KPI_AverageLayersDl','KPI_MUPairPrbRateUl','KPI_MUPairPrbRateDl','CONTEXT_AttInitalSetup','CONTEXT_SuccInitalSetup','CONTEXT_FailInitalSetup','CONTEXT_AttRelgNB','CONTEXT_AttRelgNB_Normal','CONTEXT_NbrLeft','HO_SuccExecInc','RRC_SuccConnReestab_NonSrccell','HO_SuccOutInterCuNG','HO_SuccOutInterCuXn','HO_SuccOutIntraCUInterDU','HO_SuccOutIntraDU','HO_AttOutInterCuNG','HO_AttOutInterCuXn','HO_AttOutIntraCUInterDU','HO_AttOutCUIntraDU','RRU_PuschPrbAssn','RRU_PuschPrbTot','RRU_PdschPrbAssn','RRU_PdcchCceUtil','RRU_PdcchCceAvail','Flow_NbrReqRelGnb','Flow_NbrReqRelGnb_Normal','Flow_HoAdmitFail','Flow_NbrLeft','Flow_NbrHoInc','RRC_AttConnReestab','HO_SuccOutIntraFreq','HO_AttOutExecIntraFreq','HO_SuccOutInterFreq','HO_AttOutExecInterFreq','RLC_NbrPktLossDl','RLC_NbrPktDl','MAC_NbrResErrTbUl','MAC_NbrInitTbUl','MAC_NbrTbUl','MAC_NbrResErrTbDl','MAC_NbrTbDl','MAC_NbrInitTbDl','MAC_NbrTbDl_Rank2','MAC_NbrTbDl_Rank3','MAC_NbrTbDl_Rank4','MAC_NbrInitTbUl_Qpsk','MAC_NbrInitTbUl_16Qam','MAC_NbrInitTbUl_64Qam','MAC_NbrInitTbUl_256Qam','MAC_NbrInitTbDl_Qpsk','MAC_NbrInitTbDl_16Qam','MAC_NbrInitTbDl_64Qam','MAC_NbrInitTbDl_256Qam','RRU_DtchPrbAssnUl','RRU_DtchPrbAssnDl','RRU_PdschPrbTot','MAC_CpOctUl','MAC_CpOctDl','PHY_ULMaxNL_PRB','RRC_RedirectToLTE','RRC_RedirectToLTE_EpsFB','RRC_SAnNsaConnUserMean','HoPrepAttOutEutran','HoExeSuccOutEutran','RwrEutranUeSucc','isp','ul_speed_fz','ul_speed_fm','dl_speed_fz','dl_speed_fm','PDCP_SDU_VOL_UL_plmn1','PDCP_SDU_VOL_DL_plmn1','rrc_avg_plmn1','PDCP_SDU_VOL_UL_plmn2','PDCP_SDU_VOL_DL_plmn2','rrc_avg_plmn2',
        'kpi185','kpi186','kpi187','kpi188','kpi189','kpi190','kpi191','kpi192','kpi193','kpi194','kpi195','kpi196','kpi197','kpi198','kpi199',
        'qosflow_5qi5_req','qosflow_5qi5_suc','qosflow_5qi5_suc_ratio']]
    #获取所有需要的counter名
    counters=set()
    pm=dict()
    while True:
        try:
            deal_with_kpi('11',pm,'aaaa',1)
            break
        except KeyError as e:
            pm[eval(str(e))]=1
            counters.add(eval(str(e)))
    #获取小区相关参数
    cellcsv=glob.glob(cmpath)
    cellcsv.sort()
    cell={}
    for csv in cellcsv[:]:
        logger.info(csv)
        cell_=[i.split(',') for i in open(csv,encoding='utf8').read().split('\n') if i!=''][1:]
        cell.update({i[5]:i for i in cell_})
    ctCounter={}
    for tarName in glob.glob(ctinpath):
        logger.info(tarName)
        deal_with_ct_tar(tarName,ctCounter)
    for tarName in glob.glob(cuinpath)[:]:
        logger.info(tarName)
        deal_with_tar(tarName,cell,csvList,counters,ctCounter)
    open('counters.txt','w').write(','.join(counters))
    csvName=outpath+'ericssonNrPm_'+datetime.datetime.now().strftime("%Y%m%d%H")+'.csv'
    open(csvName+'.tmp','w').write('\n'.join([','.join(i) for i in csvList]))
    os.remove(csvName) if os.path.isfile(csvName) else None
    os.rename(csvName+'.tmp',csvName)
