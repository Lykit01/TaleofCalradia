import pygame as pg
from tc_settings import *
import random,sys,os,time,re,csv,copy,gc,json
vec=pg.math.Vector2

# basic functions
class BasicTool:
    def cut_text(text,lenth):
        textArr = re.findall('.{'+str(lenth)+'}', text)
        textArr.append(text[(len(textArr)*lenth):])
        return textArr

    def ipos_in_board(ipos):
        return 0<=ipos[0]<COL_NUM and 0<=ipos[1]<ROW_NUM

    def set_color(img, color):
        color=pg.Color(*color)
        for x in range(img.get_width()):
            for y in range(img.get_height()):
                color.a = img.get_at((x, y)).a  # Preserve the alpha value.
                img.set_at((x, y), color)  # Set the color of the pixel.
    def to_three(num):
        if num>0:return 1
        elif num<0:return -1
        else:return 0

def draw_text(screen,text,font_name,size,color,x,y,align='center'):
    font=pg.font.Font(font_name,size)
    text_surface=font.render(text,True,color)
    text_rect=text_surface.get_rect()
    if align=='nw':text_rect.topleft=(x,y)
    elif align=='ne':text_rect.topright=(x,y)
    elif align=='sw':text_rect.bottomleft=(x,y)
    elif align=='se':text_rect.bottomright=(x,y)
    elif align=='n':text_rect.midtop=(x,y)
    elif align=='s':text_rect.midbottom=(x,y)
    elif align=='e':text_rect.midright=(x,y)
    elif align=='w':text_rect.midleft=(x,y)
    elif align=='center':text_rect.center=(x,y)
    else:print('wrongword')
    screen.blit(text_surface,text_rect)

def draw_bar(screen, x, y, pct):
    if pct > 0.6:col = GREEN
    elif pct > 0.3:col = YELLOW
    else:col = RED
    BAR_LENGTH = 200
    BAR_HEIGHT = 15
    fill = pct* BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    pg.draw.rect(screen, col, fill_rect)
    pg.draw.rect(screen, WHITE, outline_rect, 1)

class SpriteSheet:
    #utility class for loading and parsing spritesheet
    def __init__(self,game,filename):
        self.spritesheet=pg.image.load(os.path.join(game.img_dir, '%s.png')%filename).convert()
        with open(os.path.join(game.img_dir, '%s.json')%filename, 'r', encoding='utf-8') as f:
            self.spritesheet_json = json.load(f)
        self.spritesheet_data={}
        for frame in self.spritesheet_json['frames']:
            self.spritesheet_data[frame['filename']]=frame

    def get_image_fn(self,name='man'):
        png_name = '%s.png'%name
        if png_name not in self.spritesheet_data.keys():#没找到，用默认
            png_name='man.png'
        ff = self.spritesheet_data[png_name]['frame']
        surf_anchor=(self.spritesheet_data[png_name]['spriteSourceSize']['x'], self.spritesheet_data[png_name]['spriteSourceSize']['y'])
        if self.spritesheet_data[png_name]['rotated']:
            sz=(self.spritesheet_data[png_name]['sourceSize']['h'],self.spritesheet_data[png_name]['sourceSize']['w'])
            image = pg.Surface(sz)
            image.blit(self.spritesheet, (sz[0]-surf_anchor[1]-ff['h'],surf_anchor[0]), (ff['x'], ff['y'], ff['h'], ff['w']))
            image=pg.transform.rotate(image,90)
        else:
            image = pg.Surface((self.spritesheet_data[png_name]['sourceSize']['w'],self.spritesheet_data[png_name]['sourceSize']['h']))
            image.blit(self.spritesheet, surf_anchor, (ff['x'], ff['y'], ff['w'], ff['h']))
        image.set_colorkey(BLACK)
        return image

    def get_image(self,x,y,width,height):
        #grab an image out of a large spritesheet
        image=pg.Surface((width,height))
        image.blit(self.spritesheet,(0,0),(x,y,width,height))
        image.set_colorkey(BLACK)
        #image=pg.transform.scale(image,(width//2,height//2))#adjust size
        return image

class Skill():
    def __init__(self,game,skill):
        self.game=game
        self.skill=skill
        self.skill_info={}
        for i, ele in enumerate(self.game.skills_data[0]):
            self.skill_info[ele] = skill[i]

class Item():
    def __init__(self,game,item):
        self.game=game
        self.item=item
        self.item_info={}
        for i, ele in enumerate(self.game.items_data[0]):
            self.item_info[ele] = item[i]
        self.skill_list=eval(self.item_info['skill_list'])
        self.hurts=[int(self.item_info['puncture']),int(self.item_info['cut']),int(self.item_info['blunt']),0]

class Background(pg.sprite.Sprite):
    def __init__(self,game,x,y):
        self._layer = BG_LAYER
        self.groups = game.all_sprites, game.backgrounds
        pg.sprite.Sprite.__init__(self,self.groups)
        self.game = game
        self.image = random.choice(self.game.background_images)
        self.rect = self.image.get_rect()
        self.pos=(x,y)
        self.rect.topleft =self.pos

    def update(self):
        pass

class Tile(pg.sprite.Sprite):
    def __init__(self,game,x,y,terrain='plain'):
        self._layer = BG_LAYER
        self.groups = game.all_sprites, game.tiles
        pg.sprite.Sprite.__init__(self,self.groups)
        self.game = game
        self.terrain=terrain
        self.image_origin = self.game.spritesheet_neutral.get_image_fn('%s_terrain'%terrain)
        self.image_origin=pg.transform.scale(self.image_origin,(GRID_DIAM,GRID_DIAM))#adjust size
        self.image_accissible = self.image_origin.copy()
        self.image_accissible.blit(self.game.icon_images['tile_accessible'], (0, 0))
        self.image_attackable = self.image_origin.copy()
        self.image_attackable.blit(self.game.icon_images['tile_attackable'], (0, 0))
        self.image_selected = self.image_origin.copy()
        self.image_selected.blit(self.game.icon_images['tile_selected'], (0, 0))
        self.image=self.image_origin.copy()
        self.rect = self.image.get_rect()
        self.pos = (x, y)
        self.rect.topleft = self.pos
        self.ipos = (-99, -99)
        self.selected=False
        self.card_accessible=False
        self.card_attackable=False
        self.standing_card=None
        #移动花费
        self.tile_cost=TILE_COST_DC[terrain]
        self.tile_move_cost=self.tile_cost
        self.elevation=TILE_ELEVATION_DC[terrain]
        #地格效果
        self.tile_cond={}
        self.tile_cond['player']={'watched':0,'camp':0,'zoc':0,'lockcalvary':0}
        self.tile_cond['rival']={'watched':0,'camp':0,'zoc':0,'lockcalvary':0}

    def isclick(self, pos):
        return self.rect.collidepoint(pos)

    def update(self):
        #更新地格状态
        tp=tuple(self.ipos)
        if tp in self.game.all_read_cards_dc[self.game.selected_card_uid].accessible_tile_set:
            self.card_accessible = True
        else:
            self.card_accessible = False
        if tp in self.game.all_read_cards_dc[self.game.selected_card_uid].attackable_tile_set:
            self.card_attackable = True
            self.attackable_judge()#触发效果
        else:
            self.card_attackable = False
        #图像
        if self.card_attackable:
            self.image = self.image_attackable.copy()
        elif self.card_accessible:
            self.image=self.image_accissible.copy()
        elif self.standing_card and self.standing_card.selected:
            self.image=self.image_selected.copy()
        else:
            self.image = self.image_origin.copy()
        #特殊效果,锁骑兵
        incard=self.standing_card
        if incard and not incard.owner.inturn:
            for effect in ['lockcalvary','zoc']:
                check=incard.has_this_effect(effect)
                if check[0]:
                    for step in incard.steps:
                        x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                        if BasicTool.ipos_in_board((x,y)):
                            self.game.tile_list[x][y].tile_cond[incard.owner.get_enemy_role()][effect]=1
        if self.tile_cond[self.game.inturn_role]['lockcalvary']:
            self.tile_cost=8
        elif self.tile_cond[self.game.inturn_role]['zoc']:
            self.tile_cost=4
        else:
            self.tile_cost = TILE_COST_DC[self.terrain]
        self.tile_move_cost = self.tile_cost

    def attackable_judge(self):
        # 特殊的锁定触发-遮挡
        if self.standing_card and self.standing_card.card_cond['Sheltered']:
            self.card_attackable = False
            self.game.all_read_cards_dc[self.game.selected_card_uid].attackable_tile_set.remove(tuple(self.ipos))
            if self.card_accessible:
                self.card_accessible = False
                self.game.all_read_cards_dc[self.game.selected_card_uid].accessible_tile_set.remove(tuple(self.ipos))

    def get_order(self):
        # 场上卡牌走场的选择
        if (self.card_accessible or self.card_attackable) and not self.selected:
            self.get_selected()

    def get_selected(self):
        self.game.selected_tile.selected = False
        self.game.selected_tile=self
        self.selected=True

class Proto_Card(pg.sprite.Sprite):
    def __init__(self,game,owner,card):
        self._layer = CARD_LAYER
        self.groups = game.all_sprites, game.cards
        pg.sprite.Sprite.__init__(self,self.groups)
        self.game = game
        self.owner=owner
        self.card=card
        self.game.uid_cnt+=1
        self.uid='uid'+str(self.game.uid_cnt)
        self.game.all_read_cards_dc[self.uid]=self
        self.all_init()
    #全部初始化
    def all_init(self):
        self.card_info={}
        for i,ele in enumerate(self.game.cards_data[0]):
            if ele in ['level']:
                if self.card[i]!='':self.card_info[ele]=int(self.card[i])
            else:
                self.card_info[ele] = self.card[i]
        self.name=self.card_info['name']
        # 卡牌位置属性,default:默认,inhand:在手牌中,inboard:在场上,
        self.loc_info = 'default'
        self.pos = vec(-200, -200)
        self.ipos = [99, 99]
        self.selected = False
        self.is_general = False
        #准备、技能初始化
        self.item_init()
        self.skill_init()
        # card_cond
        self.card_cond = {'Strengthen': 0, 'Weaken': 0, 'Rumors': 0, 'Locked': 0, 'Saint': 0, 'Determined': 0,'Sheltered': 0}
        self.card_cond['Sheltered'] = 3 if 'Conceal' in self.skill_list else 0
        self.power_max=Property.BASIC_POWER+5 if 'IronBone' in self.skill_list else Property.BASIC_POWER
        self.power_max=10 if 'LowPower' in self.skill_list else self.power_max
        self.power=self.power_max
        self.strength = 2 + self.power // 5
        self.footpoint_max=max(0,Property.BASIC_FOOTPOINTS-(int(self.weapon.item_info['burden'])+int(self.armor.item_info['burden'])+int(self.shield.item_info['burden'])+int(self.vehicle.item_info['burden'])))
        self.footpoint=self.footpoint_max
        self.train_list=eval(self.card_info['train_list'])
        self.capture_prop=1 if 'BluntForce' in self.skill_list else 0.5
        #图像初始化
        self.image_init()
        #move
        self.accessible_tile_set = set()
        self.attackable_tile_set = set()
        self.front_speed=self.owner.front_speed
        self.steps=[[self.front_speed,0],[0,-1],[0,1]]#不能后退
        self.attack_times_max=int(self.weapon.item_info['attack_times'])
        self.attack_times=self.attack_times_max#攻击次数
        self.exp=0
        self.upgrade_exp=eval(self.card_info['upgrade_exp'])
        self.face_dir='face_left' if self.front_speed<0 else 'face_right'

    def item_init(self):
        self.weapon = Item(self.game,self.game.items_data_dc[self.card_info['weapon']].item)
        self.weapon.range=int(self.weapon.item_info['range'])
        self.weapon.ammo = int(self.weapon.item_info['ammo'])#弹药量
        self.weapon.accuracy =int(self.weapon.item_info['accuracy'])#准星
        self.armor =Item(self.game,self.game.items_data_dc[self.card_info['armor']].item)
        self.shield=Item(self.game,self.game.items_data_dc[self.card_info['shield']].item)
        self.vehicle=Item(self.game,self.game.items_data_dc[self.card_info['vehicle']].item)

    def skill_init(self):
        self.skill_list = eval(self.card_info['skill_list'])+self.weapon.skill_list+self.armor.skill_list+self.shield.skill_list+self.vehicle.skill_list
        self.trigger_list,self.effect_list,self.cmp_list,self.vol_list=[],[],[],[]
        self.active_skills={}
        for skill in self.skill_list:
            cskill = self.game.skills_data_dc[skill]
            if skill in ['Heal','Retreat','VillageRecruit','Tax','SellingCaptives','CallonEnemy','GrainLevies','BuildCamp']:#主动技能,当前计数、冷却时间、量
                self.active_skills[skill]={}
                self.active_skills[skill]['count'],self.active_skills[skill]['cd'],self.active_skills[skill]['vol']=0,int(cskill.skill_info['cmp']),int(cskill.skill_info['vol'])
            else:
                self.trigger_list.append(cskill.skill_info['trigger'])
                self.effect_list.append(cskill.skill_info['effect'])
                self.cmp_list.append(cskill.skill_info['cmp'])
                self.vol_list.append(cskill.skill_info['vol'])

    def image_init(self):
        #手牌图(默认状态，不变)、手牌选中图、场上图标、悬浮图(卡名、势力名、技能名(无详)、军力)、左下角详情图(全部详情，实时更新)
        self.inhand_image = self.game.icon_images['card_front'].copy()
        self.front_rect = self.inhand_image.get_rect()
        draw_text(self.inhand_image,self.card_info['cn_name'], self.game.title_font, 14, self.owner.color, 5, 8, 'nw')
        for i,skill in enumerate(self.skill_list):
            draw_text(self.inhand_image, '【%s】' % self.game.skills_data_dc[skill].skill_info['skill_name'], self.game.title_font, 12, BLACK, 5,self.front_rect.height *(2+i)// 10, 'nw')
        self.hover_image_origin = self.inhand_image.copy()  # 底稿
        self.hover_image = self.hover_image_origin.copy()
        draw_text(self.inhand_image,'%s牌 射程:%s' % (CARD_ARMBRANCH_CNNAME[self.card_info['armbranch']], self.weapon.range),self.game.title_font, 10, BLACK, 5, self.front_rect.height * 8 // 10, 'nw')
        draw_text(self.inhand_image,'阶%d hp%d 攻%d 动%d' % (self.card_info['level'],self.power,self.strength, self.footpoint),self.game.title_font, 10, BLACK, 5,self.front_rect.height * 9 // 10, 'nw')
        #选中效果
        self.inhand_image_selected=self.inhand_image.copy()
        self.inhand_image_selected.blit(self.game.icon_images['card_selected'],(0,0))
        self.image = self.inhand_image.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        #选中后详情页面
        self.detail_image_orig = pg.transform.scale(self.game.icon_images['card_front'].copy(), (int(TILE_WIDTH * 1.6), int(TILE_HEIGHT * 1.6)))
        draw_text(self.detail_image_orig, self.card_info['cn_name'], self.game.title_font, 14, self.owner.color, 5, 8, 'nw')
        self.big_rect= self.detail_image_orig.get_rect()
        ln=0
        for i,skill in enumerate(self.skill_list):
            texts = BasicTool.cut_text('【%s】%s' %(self.game.skills_data_dc[skill].skill_info['skill_name'],self.game.skills_data_dc[skill].skill_info['skill_descript']),self.big_rect.width//10)
            for t in texts:
                draw_text(self.detail_image_orig,t, self.game.title_font, 10, BLACK, 5, self.big_rect.height*(ln+2) //16, 'nw')
                ln+=1
        self.detail_image=self.detail_image_orig.copy()
        #场上图标
        self.person_image=pg.transform.scale(self.game.spritesheet_unit[self.owner.role].get_image_fn(self.name),(GRID_DIAM,GRID_DIAM))
        if self.owner.is_player_rival:
            self.person_image=pg.transform.flip(self.person_image,True,False)
        #BasicTool.set_color(self.person_image, self.owner.color)

    def become_general(self):
        self.is_general=True
        self.steps=Property.SurroundGrid4

    def change_owner(self,newowner):#牌转手的时候
        self.owner=newowner

    def change_loc_info(self,new_loc_info):
        self.loc_info=new_loc_info

    def update(self):
        self.strength= self.get_strength()
        self.get_accessible_tiles()
        #选择的动作
        if self.selected and self.loc_info in ['inboard','inhand']:
            tile=self.game.selected_tile
            if self.loc_info=='inboard':#卡牌场上行动
                self.image = self.person_image.copy()
                if tile.card_accessible:# and not tile.card_attackable:
                    self.footpoint-=tile.tile_move_cost
                    self.set_tile_pos(tile)
                    #特殊情况，骑兵行动点小于0，受到一点伤害
                    if self.footpoint<-4 and self.card_info['armbranch']=='calvary':
                        self.get_damage([0,0,0,1])
                        self.game.add_log('%s受到拒马1点伤害' % (self.card_info['cn_name']))
                elif tile.card_attackable:
                    self.attack(tile)
            elif self.loc_info=='inhand':#卡牌部署
                self.image = self.inhand_image_selected.copy()
                if tile.card_accessible and not tile.standing_card:
                    self.deploy(tile)
                elif tile.card_attackable:#战术卡直接起作用
                    self.tactic_affect(tile,int(self.vol_list[0]))
            self.game.pre_selected_tile.get_selected()
        elif self.loc_info=='inboard':
            self.image = self.person_image.copy()
        else:
            self.image=self.inhand_image.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        #悬浮图军力实时更新
        self.hover_image = self.hover_image_origin.copy()
        draw_text(self.hover_image, '%s牌 态:%s' % (CARD_ARMBRANCH_CNNAME[self.card_info['armbranch']],self.get_cond_str()), self.game.title_font,10, BLACK, 5, self.front_rect.height * 8 // 10, 'nw')
        draw_text(self.hover_image, '阶%d hp%d 攻%d 动%d 射%d' % (self.card_info['level'], self.power,self.strength,self.footpoint,self.weapon.range), self.game.title_font,10, BLACK, 5, self.front_rect.height * 9 //10, 'nw')
        #详情页面更新
        self.detail_image=self.detail_image_orig.copy()
        ammo='弹药%d'%self.weapon.ammo if self.weapon.ammo<20 else '弹药无限'
        draw_text(self.detail_image,'械【%s】刺%d切%d钝%d准%d%s' % (self.weapon.item_info['cn_name'],self.weapon.hurts[0],self.weapon.hurts[1],self.weapon.hurts[2],self.weapon.accuracy,ammo),self.game.title_font, 10, BLACK, 5, self.big_rect.height *10//16, 'nw')
        draw_text(self.detail_image,'甲【%s】刺%d切%d钝%d' % (self.armor.item_info['cn_name'], self.armor.hurts[0], self.armor.hurts[1], self.armor.hurts[2]),self.game.title_font, 10, BLACK, 5, self.big_rect.height *11//16, 'nw')
        draw_text(self.detail_image,'盾【%s】刺%d切%d钝%d' % (self.shield.item_info['cn_name'], self.shield.hurts[0], self.shield.hurts[1], self.shield.hurts[2]),self.game.title_font, 10, BLACK, 5, self.big_rect.height * 12 // 16, 'nw')
        draw_text(self.detail_image,'载【%s】刺%d切%d钝%d' % (self.vehicle.item_info['cn_name'], self.vehicle.hurts[0], self.vehicle.hurts[1], self.vehicle.hurts[2]),self.game.title_font, 10, BLACK, 5, self.big_rect.height * 13 // 16, 'nw')
        draw_text(self.detail_image,'%s牌 态:%s' % (CARD_ARMBRANCH_CNNAME[self.card_info['armbranch']], self.get_cond_str()),self.game.title_font, 10, BLACK, 5, self.big_rect.height*14//16,'nw')
        terrain=TILE_TERRAIN_CN_NAME[self.game.tile_list[self.ipos[0]][self.ipos[1]].terrain] if self.loc_info=='inboard' else ''
        draw_text(self.detail_image,'阶%dhp%d/%d攻%d动%d射%d经%d%s' % (self.card_info['level'], self.power,self.power_max,self.strength,self.footpoint,self.weapon.range,self.exp,terrain),self.game.title_font, 10, BLACK, 5, self.big_rect.height* 15//16,'nw')

        #子类的其他检查
        self.other_check()

    def attack(self,tile):
        # if self.attack_times<=0:
        #     Pow(self.game, self, '本回合攻击次数已用完')
        #     if self.game.two_computers: self.footpoint = 0
        #     if self.game.single_player and self.owner.is_player_rival: self.footpoint = 0
        #     return
        #判断是远程攻击还是近战攻击
        range_attack = 0
        if self.weapon.range>=1 and self.weapon.ammo>0:range_attack=1
        target_card = tile.standing_card
        orig_ipos=self.ipos
        #近战攻击先走到挨着，再打
        if not range_attack:
            mincoord=[999,self.ipos]
            for coord in target_card.get_surround_tile_coord('surround4')+[self.ipos]:
                dist=abs(target_card.ipos[0]-coord[0])*10+abs(target_card.ipos[1]-coord[1])*10+abs(self.ipos[0]-coord[0])+abs(self.ipos[1]-coord[1])
                if dist<mincoord[0]:mincoord=[dist,coord]
            if tuple(mincoord[1]) in self.accessible_tile_set or tuple(mincoord[1])==tuple(self.ipos):
                self.set_tile_pos(self.game.tile_list[mincoord[1][0]][mincoord[1][1]])
        # 攻击时转向
        dir = (BasicTool.to_three(tile.ipos[0] - self.ipos[0]), BasicTool.to_three(tile.ipos[1] - self.ipos[1]))
        if dir != (0, 0): self.face_dir = Property.STEP_DIRECTION_DC[dir]
        self.attack_times-=1
        self.weapon.ammo-=1#弹药-1
        self.get_exp(1)
        #骑枪冲锋
        t1, t2 = abs(target_card.ipos[0] - orig_ipos[0]), abs(target_card.ipos[1] - orig_ipos[1])
        if self.has_this_effect('LancerCharge')[0] and t1*t2==0 and t1+t2>=3 and target_card.card_info['armbranch']!='building':
            target_card.get_damage([0,0,0,target_card.power_max],self)
        else:
            target_card.get_damage(self.get_hurts(target_card,range_attack),self)
        self.attack_consume_footpoint()
        self.act_trigger('attack',target_card)
        if not tile.standing_card:#杀死对方
            self.act_trigger('kill',target_card)
            if target_card.card_info['armbranch']=='calvary':self.owner.horse_stock+=1#对面为骑兵，+1马
        #反击
        if target_card.power>0 and not range_attack and target_card.has_this_effect('fightback',tile.standing_card)[0]:
            self.get_damage(target_card.get_hurts(self,0),target_card)
        if self.power > 0 and self.loc_info=='inboard' and not tile.standing_card and not range_attack:
            self.set_tile_pos(tile)

    def attack_consume_footpoint(self):
        check=self.has_this_effect('moveafterattack')
        if check[0]:#攻击后可移动
            self.footpoint-=1
        else:#箭塔没有移动力也可以攻击
            self.footpoint = 0 if self.footpoint > 0 else -1

    def deploy(self,tile):
        if tile.tile_cond[self.game.inturn_role]['watched']:
            self.game.add_log('此地格被敌方警戒，我方无法部署，请重新选择地格。')
        elif self.owner.dinars < self.card_info['level']:
            self.game.add_log('无法部署，第纳尔不足。')
        else:
            self.owner.hand_cards.remove(self)
            discheck=self.has_this_effect('deploycostdiscount')
            discount=discheck[1] if discheck[0] else 0
            self.get_dinars(-self.card_info['level']-discount,'部署')
            self.direct_deploy(tile)
            self.act_trigger('activedeploy')
            return True
        return False

    def direct_deploy(self,tile):
        self.deploy_skill(tile)
        self.footpoint = -1 if 'Swift' not in self.skill_list else self.footpoint_max
        self.set_tile_pos(tile)
        self.change_loc_info('inboard')
        self.act_trigger('deploy')

    # 牌的部署时的技能
    def deploy_skill(self,tile):
        #全方向行动
        if 'alldirections' in self.effect_list:
            self.steps=[[1,0],[-1,0],[0,-1],[0,1]]
        #投掷斧
        throwcheck=self.has_this_effect('ThrowAxe')
        if throwcheck[0]:
            for scard in self.get_surround_card('front'):
                if scard and scard.owner.role!=self.owner.role:
                    scard.get_damage([0,0,0,throwcheck[1]])
        #大斧击退
        beatcheck = self.has_this_effect('BeatBack')
        if beatcheck[0]:
            for scard in self.get_surround_card('front'):
                if scard and scard.owner.role != self.owner.role:
                    scard.get_damage([0,0,0,beatcheck[1]])
                    scard.get_tactic_effect(['Withdraw'])

    def tactic_affect(self,tile,vol):
        if self.owner.dinars < self.card_info['level']:
            self.game.add_log('无法施展战术，第纳尔不足。')
        else:
            self.owner.hand_cards.remove(self)
            self.get_dinars(-self.card_info['level'],'施展战术:'+self.card_info['cn_name'])
            tile.standing_card.get_tactic_effect(self.skill_list,vol)
            self.get_discarded()

    def get_tactic_effect(self,skill_list,vol=0):#此处把skill传过来了，self并不是战术卡
        for skill in skill_list:
            if skill=='Assassinate':
                self.get_damage([0,0,0,self.power_max])#刺杀最大生命值
            elif skill=='Charge':
                self.footpoint=max(self.footpoint+vol,vol)#行动力为负时加冲锋也能获得移动力
            elif skill=='Supply':
                self.get_power(vol)
            elif skill=='Bargain':
                self.get_dinars(vol,'交易')
            elif skill=='Withdraw':
                x,y=self.ipos[0]-self.front_speed,self.ipos[1]
                if BasicTool.ipos_in_board((x,y)) and self.card_info['armbranch'] not in ['building'] and not self.game.tile_list[x][y].standing_card \
                        and self.game.tile_list[x][y].terrain not in ['mount']:
                    self.set_tile_pos(self.game.tile_list[x][y])
            elif skill=='MillionArrows':#注意此时self是敌方，MA就是作用于敌方全体
                for selfallcard in self.game.cards.sprites():
                    if selfallcard.loc_info=='inboard' and selfallcard.owner.role==self.owner.role:
                        selfallcard.get_damage([2,0,0,0])#2点穿刺攻击伤害
            elif skill=='HorseSupply':
                self.owner.horse_stock+=vol
            elif skill == 'CombatTrain':  # 战斗训练
                self.get_exp(vol)
            elif skill in self.card_cond.keys():#强化等状态
                if skill=='Rumors':
                    if not self.card_cond['Determined']:
                        self.card_cond['Weaken'] =vol
                        self.card_cond['Locked'] =vol
                else:
                    self.card_cond[skill]+=vol
            elif 'AllCond' in skill:#所有兵种得到状态
                ec=skill.replace('AllCond','')
                for cd in self.game.cards.sprites():
                    if cd.loc_info=='inboard' and cd.owner.role==self.owner.role:
                        cd.card_cond[ec]+=vol
            elif skill=='Conscript':#征兵
                self.owner.pick_hand_cards(vol)
            elif 'Recruit' in skill:#募兵
                cardname=skill.replace('Recruit','')
                for i in range(vol):
                    newcard = Proto_Card(self.game, self.owner, self.game.cards_data_dc[cardname])
                    self.owner.gain_hand_cards(newcard)
            elif skill == 'CaptiveEscape':  # 俘虏逃跑
                clen = len(self.owner.captive_pile)
                if clen == 0:
                    self.game.add_log('%s俘虏牌堆为空。' % (self.owner.title))
                else:
                    for i in range(vol):
                        rc = random.choice(range(clen))
                        random_captive = self.owner.captive_pile.pop(rc)
        self.game.pre_selected_card.get_selected()

    def is_in_frontier(self):
        if self.owner.is_player:return self.ipos[0]>=COL_NUM/2-0.5
        else:return self.ipos[0]<=COL_NUM/2-0.5

    def turn_pass(self):
        self.act_trigger('turn_pass')
        self.attack_times=self.attack_times_max
        self.footpoint = self.footpoint_max
        if self.is_in_frontier():self.get_exp(1)
        #主动技能冷却时间
        for askill in self.active_skills.keys():
            self.active_skills[askill]['count']+=1
        # 状态影响
        if self.card_cond['Saint']:
            self.card_cond['Determined'] += 1
            self.name='Saint'
        else:self.name=self.card_info['name']

    def turn_begin(self):
        self.act_trigger('turn_begin')
        #状态影响
        if self.card_cond['Locked']:self.footpoint=0
        #检查是否可升级
        for need in self.upgrade_exp:
            if self.exp>=need:
                Pow(self.game, self, '可升级')
                break
        #状态回合更新
        for econd in self.card_cond.keys():
            self.card_cond[econd]=max(0,self.card_cond[econd]-1)
        self.auto_act()

    def get_strength(self,target=None):
        if self.has_this_effect('MaxStrength')[0]:
            self.strength = 2 + self.power_max // 5
        else:
            self.strength = 2 + self.power // 5
        #增加攻击力
        strength=1 + self.power // 10
        check0=self.has_this_effect('strengthrise',target)
        if check0[0]:
            self.strength+=check0[1]
        #状态影响
        if self.card_cond['Strengthen']:strength+=1
        if self.card_cond['Saint'] and self.power<self.power_max:strength+=1
        if self.card_cond['Weaken']:strength-=1
        return self.strength

    def get_hurts(self,target,range_attack=0):
        strength=self.get_strength(target)
        # 后面攻击，+2，侧翼攻击+1
        if self.face_dir == target.face_dir:
            self.game.add_log('%s【背后攻击】:攻击加成+2' % (self.card_info['cn_name']))
            active_plus = 2
        elif self.face_dir == Property.DIRECTION_OPPO[target.face_dir]:
            active_plus = 0
        else:
            self.game.add_log('%s【侧翼攻击】:攻击加成+1' % (self.card_info['cn_name']))
            active_plus = 1
        opts=[]
        for i in range(3):
            tmp=[0]*4
            if self.weapon.hurts[i]!=0:
                tmp[i] = self.weapon.hurts[i] + self.vehicle.hurts[i] + strength+active_plus
                opts.append(tmp)
        if not opts:opts.append([0]*4)
        hurts=random.choice(opts)
        # 远程的准星下限0.7
        if range_attack and random.random()*10 >= self.weapon.accuracy:
            Pow(self.game, self, '未射中！')
            hurts[0]=0
        return hurts

    def get_defence(self):
        return [self.armor.hurts[0]+max(0,self.shield.hurts[0]),self.armor.hurts[1]+max(0,self.shield.hurts[1]),
                self.armor.hurts[2]+max(0,self.shield.hurts[2]),0]

    #damage type 0:puncture 1:cut,2:blunt,3:直接伤害
    def get_damage(self,hurts,source=None):
        #hurts[1,1,2,0]
        hdc={0:'刺伤',1:'割伤',2:'钝伤',3:'真伤'}
        for i in range(4):
            if hurts[i]!=0:
                break
        defences=self.get_defence()
        realhurts=[max(hurts[0]-defences[0],0),max(hurts[1]-defences[1],0),max(hurts[2]-defences[2],0),max(hurts[3]-defences[3],0)]
        self.shield.hurts=[max(0,self.shield.hurts[0]-hurts[0]),max(0,self.shield.hurts[1]-hurts[1]),max(0,self.shield.hurts[2]-hurts[2]),0]
        damage=sum(realhurts)
        #减伤
        check0 = self.has_this_effect('damagereduce')
        if check0[0] and not (source and source.has_this_effect('ignoredamagereduce')[0]):#对面可能有无视减伤的技能
            damage += check0[1]
        if damage<0:damage=0
        self.power-=damage
        if damage:Pow(self.game, self, '%s:%d'%(hdc[i],-damage),-damage)
        else:Pow(self.game, self, '未造成伤害',0)
        if self.power<=0:
            self.game.tile_list[self.ipos[0]][self.ipos[1]].standing_card = None
            self.act_trigger('killed')
            self.game.pre_selected_card.get_selected()
            #复仇技能
            recheck=self.has_this_effect('Revenge')
            if source and recheck[0]:source.get_damage([0,0,0,recheck[1]])
            #如果是近战伤害，有30%概率被俘
            if self.card_info['armbranch'] not in ['building'] and source and source.power>0 and random.random()<=source.capture_prop:
                self.get_captured()
            else:
                self.get_discarded()

    def get_power(self,add=0):
        real_add=min(self.power_max,self.power+add)-self.power
        self.power +=real_add
        Pow(self.game, self, '恢复：%d'%real_add, real_add)

    def get_exp(self,add=0,showpow=1):
        self.exp += add
        if showpow:Pow(self.game, self, '%d exp'%(add),add)

    def get_dinars(self,add=0,fromskill=None,showpow=1):
        self.owner.dinars += add
        if showpow:Pow(self.game, self, '%d dinars' % (add),add)
        if fromskill:
            self.game.add_log('%s【%s】:第纳尔变化%d'%(self.owner.title,fromskill,add))

    def get_clout(self,add=0):
        pass

    def get_order(self):
        scard=self.game.all_read_cards_dc[self.game.selected_card_uid]
        #作用于己方的战术卡选中时，不能切换为场上的士兵
        if not self.selected and self.owner.inturn and self.loc_info in ['inhand','inboard'] and not ('self' in scard.card_info['target'] and self.loc_info=='inboard'):
            self.get_selected()

    def get_selected(self):
        # 重新选择卡片后，选择的地格也要还原
        self.game.pre_selected_tile.get_selected()
        #卡片选择
        self.game.all_read_cards_dc[self.game.selected_card_uid].selected=False
        self.game.selected_card_uid=self.uid
        self.selected=True

    def get_accessible_tiles(self):
        #bfs,找出所有能到达的点
        self.accessible_tile_set=set()
        self.attackable_tile_set=set()
        if self.loc_info=='inboard':
            random.shuffle(self.steps)
            queue=[[[self.ipos[0],self.ipos[1]],0]]
            visited = [[0] * ROW_NUM for _ in range(COL_NUM)]
            visited[self.ipos[0]][self.ipos[1]]=1
            while queue:
                tmpque=[]
                while queue:
                    tmpa=queue.pop()
                    tmp,depth=tmpa[0],tmpa[1]
                    if depth<self.footpoint:
                        for step in self.steps:
                            x,y=tmp[0]+step[0],tmp[1]+step[1]
                            if BasicTool.ipos_in_board([x,y]) and not visited[x][y] and self.game.tile_list[x][y].terrain!='mount':
                                visited[x][y]=1
                                if self.game.tile_list[x][y].standing_card==None:
                                    tmpque.append([[x,y],depth+self.game.tile_list[x][y].tile_cost])
                                    self.accessible_tile_set.add((x,y))
                                    self.game.tile_list[x][y].tile_move_cost=depth+self.game.tile_list[x][y].tile_cost
                                elif self.game.tile_list[x][y].standing_card.owner.role == self.owner.role:#己方单位占领区，可通过
                                    tmpque.append([[x, y], depth + self.game.tile_list[x][y].tile_cost])
                                    self.game.tile_list[x][y].tile_move_cost = depth + self.game.tile_list[x][y].tile_cost
                                elif self.game.tile_list[x][y].standing_card.owner.role != self.owner.role:
                                    scd=self.game.tile_list[tmp[0]][tmp[1]].standing_card
                                    if scd and scd.owner.role == self.owner.role and scd!=self:
                                        pass
                                    else:
                                        #self.accessible_tile_set.add((x,y))
                                        if not (self.weapon.range>0 and self.weapon.ammo>0) and self.attack_times>0:self.attackable_tile_set.add((x,y))#近战才能直接跑过去攻击
                queue=tmpque
                queue.sort(key=lambda x:x[1])
            #远程寻找攻击范围内的敌人,也采取bfs的方式，因为会有高山阻隔
            if (self.attack_times>0 and self.footpoint>0 and self.weapon.range>0 and self.weapon.ammo>0) or (self.attack_times>0 and self.footpoint==0 and self.card_info['armbranch'] in ['building']):#有行动点才能找,建筑要求为0时可以攻击
                steps=Property.SurroundGrid4
                queue = [[[self.ipos[0], self.ipos[1]], 0]]
                visited = [[0] * ROW_NUM for _ in range(COL_NUM)]
                visited[self.ipos[0]][self.ipos[1]] = 1
                while queue:
                    tmpque = []
                    while queue:
                        tmpa = queue.pop()
                        tmp, depth = tmpa[0], tmpa[1]
                        if depth < self.weapon.range:
                            for step in steps:
                                x, y = tmp[0] + step[0], tmp[1] + step[1]
                                if BasicTool.ipos_in_board([x, y]) and not visited[x][y] and self.game.tile_list[x][y].terrain != 'mount':
                                    visited[x][y] = 1
                                    tmpque.append([[x, y], depth+1])
                                    if self.game.tile_list[x][y].standing_card and self.game.tile_list[x][y].standing_card.owner.role != self.owner.role:
                                        self.attackable_tile_set.add((x, y))
                    queue = tmpque
        elif self.loc_info=='inhand':#可部署区域
            if self.card_info['armbranch']=='tactic':
                self.search_tactic_target()
            else:
                for i in range(COL_NUM):
                    for j in range(ROW_NUM):
                        tile=self.game.tile_list[i][j]
                        if tile.tile_cond[self.owner.role]['camp'] and not tile.tile_cond[self.owner.role]['watched'] and not tile.standing_card and tile.terrain!='mount':
                            self.accessible_tile_set.add((i,j))

    def search_tactic_target(self):
        if 'enemy' in self.card_info['target']:
            select_enemy_all=True if 'all' in self.card_info['target'] else False
            for i in range(COL_NUM):
                for j in range(ROW_NUM):
                    scard=self.game.tile_list[i][j].standing_card
                    if select_enemy_all:
                        if scard and scard.owner.role!=self.owner.role and scard.card_info['armbranch']!='building':
                            self.attackable_tile_set.add((i, j))
                    else:#不选将军
                        if scard and not scard.is_general and scard.owner.role!=self.owner.role and scard.card_info['armbranch']!='building':
                            self.attackable_tile_set.add((i, j))
        elif 'self' in self.card_info['target']:
            exc_armbranch=[]
            if 'non' in self.card_info['target']:exc_armbranch=self.card_info['target'].split('non')[1:]
            select_self_all=True if 'all' in self.card_info['target'] else False
            for i in range(COL_NUM):
                for j in range(ROW_NUM):
                    scard=self.game.tile_list[i][j].standing_card
                    if select_self_all:
                        if scard and scard.owner.role==self.owner.role and scard.card_info['armbranch'] not in ['building']+exc_armbranch:
                            self.attackable_tile_set.add((i, j))
                    else:#不选将军
                        if scard and not scard.is_general and scard.owner.role==self.owner.role and scard.card_info['armbranch'] not in ['building']+exc_armbranch:
                            self.attackable_tile_set.add((i, j))

    def set_tile_pos(self,tile):
        if self.loc_info=='inboard':
            self.game.tile_list[self.ipos[0]][self.ipos[1]].standing_card = None
            self.act_trigger('move')
            dir = (BasicTool.to_three(tile.ipos[0] - self.ipos[0]), BasicTool.to_three(tile.ipos[1] - self.ipos[1]))
            if dir != (0, 0): self.face_dir = Property.STEP_DIRECTION_DC[dir]
        #if tile.standing_card:print('cover',tile.standing_card.name,self.name)#查bug
        tile.standing_card=self
        self.set_pos(tile.pos)
        self.ipos=tile.ipos

    def set_pos(self,pos):
        self.pos = pos
        self.rect.topleft = self.pos

    def isclick(self, pos):
        return self.rect.collidepoint(pos)

    def has_this_effect(self,act,target=None):
        if self.loc_info=='inboard' and act in self.effect_list:
            idx=self.effect_list.index(act)
            skill = self.skill_list[idx]
            if not self.cmp_list or self.cmp_list[idx]=='':
                return [True, int(self.vol_list[idx])]
            elif target and self.cmp_list[idx]=='levelcmp':
                if target.card_info['level']>self.card_info['level']:
                    return [True,int(self.vol_list[idx])]
            elif target and self.cmp_list[idx]=='powercmp2':
                if target.power>self.power:
                    return [True,int(self.vol_list[idx])]
            elif target and self.cmp_list[idx]=='levelrange1':#按军阶划分等级
                return [True,min((target.card_info['level']-1)//3+1,3)]
            elif target and self.cmp_list[idx]=='powercmp':
                if target.power<self.power:
                    return [True,int(self.vol_list[idx])]
            elif 'boardexist' in self.cmp_list[idx]:
                findname=self.cmp_list[idx].replace('boardexist','')
                for card in self.game.cards.sprites():
                    if card.name==findname and card.loc_info=='inboard':
                        return [True, int(self.vol_list[idx])]
            elif target and 'antiarmbranch' in self.cmp_list[idx]:
                armbranch=self.cmp_list[idx].replace('antiarmbranch','')
                if target and target.card_info['armbranch']==armbranch:
                    return [True, int(self.vol_list[idx])]
            elif self.cmp_list[idx]=='ScatterArray':
                findname = self.name
                for card in self.game.cards.sprites():
                    if card.name == findname and card.loc_info == 'inboard' and card.owner.role==self.owner.role and card.ipos!=self.ipos:
                        return [True, int(self.vol_list[idx])]
            elif self.cmp_list[idx]=='DenseArray':
                findname = self.name
                for card in self.game.cards.sprites():
                    if card.name == findname and card.loc_info == 'inboard' and card.owner.role==self.owner.role and abs(card.ipos[0]-self.ipos[0])+abs(card.ipos[1]-self.ipos[1])==1:
                        return [True, int(self.vol_list[idx])]
            elif 'dicediv' in self.cmp_list[idx]:#骰子划分区间
                num=int(self.cmp_list[idx].replace('dicediv',''))
                if random.randint(1,6)<=num:
                    vol=-int(self.vol_list[idx])
                else:
                    vol = int(self.vol_list[idx])
                volstr=str(vol) if vol<=0 else '+'+str(vol)
                self.game.add_log('%s发动【%s】:变化结果%s'%(self.card_info['cn_name'], self.game.skills_data_dc[skill].skill_info['skill_name'],volstr))
                return [True, vol]
            elif 'diceless' in self.cmp_list[idx]:#骰子命中点数
                num=int(self.cmp_list[idx].replace('diceless',''))
                if random.randint(1,6)<=num:
                    vol=int(self.vol_list[idx])
                else:
                    vol = 0
                self.game.add_log('%s发动【%s】:变化结果+%d'%(self.card_info['cn_name'], self.game.skills_data_dc[skill].skill_info['skill_name'],vol))
                return [True, vol]
            elif 'tileterrain' in self.cmp_list[idx]:
                findtile = self.cmp_list[idx].replace('tileterrain','')
                if self.game.tile_list[self.ipos[0]][self.ipos[1]].terrain==findtile:
                    return [True,int(self.vol_list[idx])]
        return [False,0]
    def act_trigger(self,act,target=None):
        if act in self.trigger_list:
            idx=self.trigger_list.index(act)
            check=self.has_this_effect(self.effect_list[idx],target)
            if check[0]:
                self.complete_act(self.skill_list[idx],self.effect_list[idx],check[1],target)
        #一些动作的直接影响
        if act=='kill':#杀敌获取经验
            self.get_exp(2*target.card_info['level'])

    def complete_act(self,skill,effect,vol,target=None):
        if effect=='getfootpoint':
            self.footpoint+=vol
        elif effect=='getdinar':
            self.get_dinars(vol,skill,1)
        elif effect=='watchtile4link':
            for step in Property.SurroundGrid4:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)):
                    self.game.tile_list[x][y].tile_cond[self.owner.get_enemy_role()]['watched']+=vol
        elif effect=='watchtile8link':
            for step in Property.SurroundGrid8:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)):
                    self.game.tile_list[x][y].tile_cond[self.owner.get_enemy_role()]['watched']+=vol
        elif effect=='watchtile24link':
            for step in Property.SurroundGrid24:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)):
                    self.game.tile_list[x][y].tile_cond[self.owner.get_enemy_role()]['watched']+=vol
        elif effect=='camptile24link':
            for step in Property.SurroundGrid24:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)):
                    self.game.tile_list[x][y].tile_cond[self.owner.role]['camp']+=vol
        elif effect=='camptile8link':
            for step in Property.SurroundGrid8:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)):
                    self.game.tile_list[x][y].tile_cond[self.owner.role]['camp']+=vol
        elif effect=='copy4link':
            for step in Property.SurroundGrid4:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)) and not self.game.tile_list[x][y].standing_card:
                    copycard=Proto_Card(self.game,self.owner,self.card)
                    copycard.direct_deploy(self.game.tile_list[x][y])
                    return
        elif 'pet' in effect:
            pet=effect.replace('pet','')
            for step in Property.SurroundGrid8:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)) and not self.game.tile_list[x][y].standing_card and self.game.tile_list[x][y].terrain!='mount':
                    petcard=Pet(self.game,self.owner,self.game.cards_data_dc[pet])
                    petcard.direct_deploy(self.game.tile_list[x][y])
                    petcard.appoint_master(self)
                    return
        elif effect=='splash4link':
            for step in Property.SurroundGrid4:
                x,y=self.ipos[0]+step[0],self.ipos[1]+step[1]
                if BasicTool.ipos_in_board((x,y)) and self.game.tile_list[x][y].standing_card:
                    sd=self.game.tile_list[x][y].standing_card
                    if sd.uid!=target.uid and sd.owner.role!=self.owner.role:
                        sd.get_damage(self.get_hurts(sd,1))
        elif effect=='Penetrate':#穿刺
            for cd in target.get_surround_card('back'):
                if cd and cd.owner.role != self.owner.role:
                    cd.get_damage(self.get_hurts(cd,1))
        elif effect=='withdraw':
            self.get_tactic_effect(['Withdraw'])
        elif 'insummon' in effect:#原地召唤
            card=effect.replace('insummon','')
            summoncard = Proto_Card(self.game, self.owner, self.game.cards_data_dc[card])
            summoncard.direct_deploy(self.game.tile_list[self.ipos[0]][self.ipos[1]])
        elif 'getcond' in effect:
            cond=effect.replace('getcond','')
            self.card_cond[cond]+=vol
        elif 'disposecond' in effect:
            cond=effect.replace('disposecond','')
            self.card_cond[cond]=vol
        elif effect=='BackShelter':
            for cd in self.get_surround_card('back'):
                if cd:cd.card_cond['Sheltered']+=1
        elif effect in ['Locked']:
            target.card_cond[effect]+=vol

    def get_surround_card(self,pt='back'):
        if pt in ['back','front']:
            xadd=self.front_speed if pt=='front' else -self.front_speed
            x, y = self.ipos[0]+xadd, self.ipos[1]
            if BasicTool.ipos_in_board((x, y)):
                scard = self.game.tile_list[x][y].standing_card
                if scard:return [scard]
        return []

    def get_surround_tile_coord(self,pt='surround4'):
        res=[]
        if pt == 'surround4':
            for step in Property.SurroundGrid4:
                x, y = self.ipos[0] + step[0], self.ipos[1] + step[1]
                if BasicTool.ipos_in_board((x, y)) and not self.game.tile_list[x][y].standing_card:
                    res.append((x,y))
        return res

    #俘虏和弃牌
    def get_captured(self):
        self.clear_standing_tile()
        self.owner.get_enemy().captive_pile_append(self)
    def get_discarded(self):
        if self.selected:self.game.pre_selected_card.get_selected()
        self.clear_standing_tile()
        self.owner.discard_pile_append(self)

    def clear_standing_tile(self):
        if BasicTool.ipos_in_board(self.ipos) and self.game.tile_list[self.ipos[0]][self.ipos[1]].standing_card==self:
            self.game.tile_list[self.ipos[0]][self.ipos[1]].standing_card = None

    def get_cond_str(self):
        res=''
        for ec in self.card_cond.keys():
            if self.card_cond[ec]:
                res=res+COND_CN_NAME_DC[ec]+' '
        return res

    #晋升
    def upgrade(self,totype=0):
        if self.train_list[totype]!='':
            if self.owner.dinars<self.card_info['level']:
                self.game.add_log('第纳尔不足，%s无法晋升。' % (self.card_info['cn_name']))
                return
            elif totype==2 and self.owner.horse_stock<1:
                self.game.add_log('马匹不足，%s无法晋升。' % (self.card_info['cn_name']))
                return
            Pow(self.game, self, 'LEVEL UP')
            self.footpoint=-1
            self.get_exp(-self.upgrade_exp[totype],0)
            self.get_dinars(-self.card_info['level'],'晋升',0)
            if totype == 2:self.owner.horse_stock-=1
            upcard = Proto_Card(self.game, self.owner, self.game.cards_data_dc[self.train_list[totype]])
            upcard.direct_deploy(self.game.tile_list[self.ipos[0]][self.ipos[1]])
            self.game.add_log('%s晋升为%s。' % (self.card_info['cn_name'],upcard.card_info['cn_name']))
            upcard.exp=self.exp
            self.get_discarded()#回收
        else:
            self.game.add_log('%s无法晋升。' % (self.card_info['cn_name']))

    def auto_act(self):
        pass

    def other_check(self):
        pass

    def draw_health(self):
        rate=self.power/self.power_max
        if rate>=0.7:col=GREEN
        elif rate>=0.3:col=YELLOW
        else:col=RED
        barh=7
        self.health_bar=pg.Rect(0,self.rect.height-barh,int(self.rect.width*rate),barh)
        if rate<1:pg.draw.rect(self.image,col,self.health_bar)

    def __str__(self):
        return self.card

    __repr__ = __str__

class Pet(Proto_Card):
    def appoint_master(self,master):
        self.master=master
        self.steps=Property.SurroundGrid4

    def auto_act(self):
        self.get_accessible_tiles()
        if self.attackable_tile_set:
            atk=random.choice(list(self.attackable_tile_set))
            self.attack(self.game.tile_list[atk[0]][atk[1]])
            if self.attack_times<1:
                return
        if self.accessible_tile_set:
            acclist=list(self.accessible_tile_set)
            mpos=self.master.ipos
            random.shuffle(acclist)
            acclist.sort(key=lambda x:abs(mpos[0]-x[0])+abs(mpos[1]-x[1]))
            self.set_tile_pos(self.game.tile_list[acclist[0][0]][acclist[0][1]])
            self.footpoint=0

    def other_check(self):
        if not self.master.alive():
            self.get_discarded()

class Button(pg.sprite.Sprite):
    def __init__(self,game,name,pos):
        self._layer = EFFECT_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self,self.groups)
        self.game = game
        self.name=name
        self.image =pg.transform.scale(self.game.spritesheet_neutral.get_image_fn(name),(BUTTON_DIAM,BUTTON_DIAM))
        self.rect = self.image.get_rect()
        self.pos_orig=pos
        self.pos = self.pos_orig
        self.rect.topleft = self.pos
        self.get_extra_filter()

    def get_extra_filter(self):
        self.is_skill=False

    def isclick(self, pos):
        return self.rect.collidepoint(pos)

    def get_order(self):
        if self.name=='next_turn':
            self.game.game_turn_pass()
        elif self.name=='restart_game':
            self.game.playing=False

#升级按钮
class Upgrade_Button(Button):
    def get_extra_filter(self):
        self.is_skill=True

    def get_order(self):
        self.game.all_read_cards_dc[self.game.selected_card_uid].upgrade(int(self.name[-1]))

    def update(self, *args):
        selcard = self.game.all_read_cards_dc[self.game.selected_card_uid]
        if selcard and selcard.loc_info == 'inboard' and selcard.card_info['armbranch'] in ['calvary',
            'infantry','archer'] and selcard.exp>=selcard.upgrade_exp[int(self.name[-1])] and selcard.footpoint>0:
            self.pos = self.pos_orig
        else:
            self.pos=(-200,-50)
        self.rect.topleft = self.pos

class Askill_Button(Button):
    def get_extra_filter(self):
        self.is_skill = True
        tile_filter_dc={'VillageRecruit':['village'],'Tax':['village'],'SellingCaptives':['village'],'CallonEnemy':['village'],'GrainLevies':['village'],'BuildCamp':['plain']}
        if self.name in tile_filter_dc.keys():
            self.tile_filters=tile_filter_dc[self.name]
        else:
            self.tile_filters=TILE_TERRAINS+['village']

    def get_order(self):
        selcard = self.game.all_read_cards_dc[self.game.selected_card_uid]
        if self.name=='Heal':
            selcard.get_power(selcard.active_skills[self.name]['vol'])
        elif self.name=='Retreat':
            selcard.get_tactic_effect(['Withdraw'])
        elif self.name=='VillageRecruit':
            for i in range(selcard.active_skills[self.name]['vol']):
                newcard = Proto_Card(self.game, selcard.owner, self.game.cards_data_dc[CAMP_NEWMAN_DC[selcard.owner.card_info['camp']]])
                selcard.owner.gain_hand_cards(newcard)
        elif self.name=='Tax':
            selcard.get_dinars(selcard.active_skills[self.name]['vol'],'征税')
        elif self.name=='GrainLevies':
            for i in range(selcard.active_skills[self.name]['vol']):
                selcard.owner.gain_hand_cards(Proto_Card(self.game, selcard.owner, self.game.cards_data_dc['Wheat']))
            selcard.get_dinars(-selcard.active_skills[self.name]['vol'],'征粮')
        elif self.name=='SellingCaptives':# 卖俘虏
            money = 0
            while selcard.owner.captive_pile:
                sold=selcard.owner.captive_pile.pop()
                money += self.game.all_read_cards_dc[sold].card_info['level']
                self.game.all_read_cards_dc[sold].get_discarded()
            selcard.get_dinars(money, '卖俘虏')
        elif self.name=='CallonEnemy':#招降俘虏
            clen=len(selcard.owner.captive_pile)
            if clen==0:
                self.game.add_log('%s俘虏牌堆为空。' % (selcard.owner.title))
            else:
                for i in range(selcard.active_skills[self.name]['vol']):
                    rc=random.choice(range(clen))
                    random_captive_uid=selcard.owner.captive_pile.pop(rc)
                    capcard=self.game.all_read_cards_dc[random_captive_uid]
                    capcard.all_init()
                    selcard.owner.gain_hand_cards(capcard)
        elif self.name == 'BuildCamp':  # 修建营地
            selcard.get_dinars(-selcard.active_skills[self.name]['vol'], '修营地')
            campcard = Proto_Card(self.game, selcard.owner, self.game.cards_data_dc['Campsite'])
            campcard.direct_deploy(self.game.tile_list[selcard.ipos[0]][selcard.ipos[1]])
            selcard.get_discarded()
        selcard.footpoint=0
        selcard.active_skills[self.name]['count']=0
        self.game.pre_selected_card.get_selected()

    def update(self, *args):
        selcard = self.game.all_read_cards_dc[self.game.selected_card_uid]
        if selcard and selcard.loc_info == 'inboard' and self.name in selcard.skill_list and selcard.footpoint>0 \
                and selcard.active_skills[self.name]['count']>=selcard.active_skills[self.name]['cd'] \
                and self.game.tile_list[selcard.ipos[0]][selcard.ipos[1]].terrain in self.tile_filters:
            self.pos = self.pos_orig
        else:
            self.pos = (-200, -50)
        self.rect.topleft = self.pos

#装饰效果类
class Pow(pg.sprite.Sprite):
    def __init__(self,game,owner,content,form=0):
        self._layer = EFFECT_LAYER
        self.groups = game.all_sprites,game.pows
        pg.sprite.Sprite.__init__(self,self.groups)
        self.game = game
        self.owner=owner
        self.color=BLACK
        self.content = content
        if form>0:
            self.color=GREEN
            self.content='+'+content
        else:
            self.color=RED
        self.font_size=25
        self.radius=100
        self.image = pg.Surface([self.radius*2, self.radius*2])  # 设置透明surface的方法，方便在上面作画
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.pos = self.owner.pos[0]+self.owner.rect.width//2,self.owner.pos[1]+self.owner.rect.height//2
        self.rect.center = self.pos
        self.lifespan=1000
        self.spown_time = pg.time.get_ticks()

    def update(self, *args):
        if pg.time.get_ticks()-self.spown_time>self.lifespan:
            self.kill()
            del self
            gc.collect()



