#!/usr/bin/env python
# -*- coding:utf-8 -*-
#game options
TITLE='TaleofCalradia'
SIZE=WIDTH,HEIGHT=1400, 990
BG_SIZE=[WIDTH, HEIGHT]
FPS=60
FONT_NAME='arial'
HS_FILE='highscore.txt'
CARD_FILE='cards_data.csv'
SKILL_FILE='skills_data.csv'
ITEM_FILE='items_data.csv'
MAXINT=100000000

#地块标点，均为nw
ROW_NUM,COL_NUM=9,13
ANCHOR=[20,30]
GRID_DIAM=80
TILE_WIDTH,TILE_HEIGHT=94,141
TILE_GAP=1
KX=ANCHOR[0]+TILE_WIDTH+TILE_GAP+COL_NUM*(GRID_DIAM+TILE_GAP)
KY=ANCHOR[1]+2*(TILE_GAP+GRID_DIAM)

PLAYER_GENERAL_ANCHOR=[ANCHOR[0],KY]
TILE_ANCHOR=[ANCHOR[0]+TILE_WIDTH+TILE_GAP,ANCHOR[1]]
ENEMY_GENERAL_ANCHOR=[KX,KY]

PLAYER_DISCARD_ANCHOR=ANCHOR
ENEMY_DISCARD_ANCHOR=[ANCHOR[0]+(1+COL_NUM)*(GRID_DIAM+TILE_GAP),ANCHOR[1]]

PLAYER_CAPTIVE_ANCHOR=[ANCHOR[0],ANCHOR[1]+(ROW_NUM-2)*(GRID_DIAM+TILE_GAP)]
ENEMY_CAPTIVE_ANCHOR=[KX,ANCHOR[1]+(ROW_NUM-2)*(GRID_DIAM+TILE_GAP)]

HAND_CARDS_ANCHOR=[ANCHOR[0]+4*GRID_DIAM+TILE_GAP,ANCHOR[1]+ROW_NUM*(GRID_DIAM+TILE_GAP)]
CARD_DETAIL_ANCHOR=[ANCHOR[0],ANCHOR[1]+ROW_NUM*(GRID_DIAM+TILE_GAP)]

TURN_SIGN_ANCHOR=[WIDTH//2,ANCHOR[1]//2]

BUTTON_DIAM=50
NEXT_TURN_BUTTON_ANCHOR=[KX,ANCHOR[1]+ROW_NUM*(TILE_GAP+GRID_DIAM)]
EXPLAIN_BUCKET_POS=[KX,NEXT_TURN_BUTTON_ANCHOR[1]+BUTTON_DIAM]
#技能按钮
SKILL_BUTTON_ANCHOR=[ANCHOR[0]+2*GRID_DIAM,ANCHOR[1]+ROW_NUM*(GRID_DIAM+TILE_GAP)]
#方向等标志物
SMALL_DIAM=30

class Property:
    #基本属性
    BASIC_POWER=20
    BASIC_FOOTPOINTS=3
    #周围单元格
    SurroundGrid4 = [[0,1],[0,-1],[1,0],[-1,0]]
    STEP_DIRECTION_DC={(-1,0):'face_left',(-1,-1):'face_left',(-1,1):'face_left',(1,0):'face_right',(1,1):'face_right',(1,-1):'face_right',(0,-1):'face_up',(0,1):'face_down'}
    DIRECTION_OPPO={'face_left':'face_right','face_right':'face_left','face_up':'face_down','face_down':'face_up'}
    DIRPOS = {'face_left': (0, GRID_DIAM // 6),'face_right': (GRID_DIAM - SMALL_DIAM, GRID_DIAM // 6),
              'face_up': (GRID_DIAM // 2 - SMALL_DIAM // 2, 0),'face_down': (GRID_DIAM // 2 - SMALL_DIAM // 2, GRID_DIAM - SMALL_DIAM)}
    SurroundGrid8 = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]
    SurroundGrid24=[[i,j] for i in range(-2,3) for j in range(-2,3)]

#TILE property
TILE_TERRAINS=['plain','hill','water','snow','sand']
TILE_COST_DC={'plain':1,'hill':2,'water':4,'snow':1,'sand':1,'mount':999,'village':1}
TILE_ELEVATION_DC={'plain':1,'hill':2,'water':0,'snow':1,'sand':1,'mount':3,'village':1}
TILE_TERRAIN_CN_NAME={'plain':'平原','hill':'丘陵','water':'水岸','snow':'雪地','sand':'沙地','mount':'山地','village':'村庄'}

#CAMP_INFO
CAMP_LINK_TERRAIN_DC={'Swadia':'plain','Rohdok':'hill','Nord':'water','Sarranid':'sand','Vagire':'snow','Khergit':'plain'}
CAMP_NEWMAN_DC={'Swadia':'S.Newman','Rohdok':'R.Tribesman','Nord':'N.Newman','Sarranid':'Sr.Newman','Vagire':'V.Newman','Khergit':'K.Tribesman'}

#CARD property

HAND_CARDS_INIT_MAX=5#初始手牌上限
HAND_CARD_MAX=10#手牌上限
CARD_ARMBRANCH_CNNAME={'archer':'射手','calvary':'骑兵','infantry':'步兵','general':'将军','tactic':'战术','building':'建筑'}
COND_CN_NAME_DC={'Strengthen':'强化','Weaken':'弱化','Rumors':'流言','Locked':'眩晕','Saint':'圣徒','Determined':'坚定','Sheltered':'遮挡'}
#turns
TURN_DINARS=2
TURN_EXPLAIN_NUM=5

#player property
OTHER_ASSETS=['check','finish']

#background properties
SCROLL_VEL=[0,1]

#layer数值越大越在上面
EFFECT_LAYER=3
CHARACTER_LAYER=2
CARD_LAYER=2
DEFAULT_LAYER=2
UI_LAYER=1
BG_LAYER=0


#colors
WHITE=(255,255,255)
BLACK=(0,0,0)
RED=(255,0,0)
DARKRED=(116,0,0)#敌军颜色
GREEN=(0,255,0)
BLUE=(0,0,255)#我军颜色
TURKEYBLUE=(0,199,140)#友军颜色
YELLOW=(255,255,0)
GOLDYELLOW=(255,215,0)#中立颜色
LIGHTBLUE=(0,155,155)
BGCOLOR=BLACK










