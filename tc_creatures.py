from tc_basics import *
from astar import *

#角色
class Creature(pg.sprite.Sprite):
    def __init__(self,game,name=None):
        self._layer = DEFAULT_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.name = name
        self.turns_num = 0
        self.inturn = False
        self.role = 'rival'
        self.title='title'

        #角色对应的卡牌属性
        card=self.game.cards_data_dc[name]
        self.card = card
        self.card_info = {}
        for i, ele in enumerate(self.game.cards_data[0]):
            if ele in ['level']:
                if card[i] != '': self.card_info[ele] = int(card[i])
            else:
                self.card_info[ele] = card[i]
        self.power_max=Property.BASIC_POWER
        self.power=self.power_max

        #牌组
        self._hand_cards_init_max = HAND_CARDS_INIT_MAX  # 初始手牌上限
        self._hand_cards_max = HAND_CARD_MAX  # 手牌上限
        self.hand_cards = []  # 当前手牌
        self.discard_pile = []  # 弃牌堆
        self.captive_pile=[]
        #出牌费用上限
        self.dinars=50000
        self.turn_dinars=TURN_DINARS
        self.maintain_dinars=0
        self.horse_stock=2
        #玩家信息
        self.is_player=False
        self.is_player_rival=False
        self.general_card=None
        self.image_init()
        self.color=BLACK
        self.front_speed=1

    def become_player(self, player_name="None"):
        self.role='player'
        self.is_player = True
        self.title = "玩家 "+self.card_info['cn_name']
        self.pos=vec(PLAYER_GENERAL_ANCHOR)
        self.rect.topleft=self.pos
        self.discard_pile_anchor=PLAYER_DISCARD_ANCHOR
        self.captive_pile_anchor=PLAYER_CAPTIVE_ANCHOR
        self.color=BLUE
        self.same_init(1)

    def become_player_rival(self):
        self.role='rival'
        self.is_player_rival= True
        self.title = "对手 " + self.card_info['cn_name']
        self.front_speed = -1
        self.pos = vec(ENEMY_GENERAL_ANCHOR)
        self.rect.topleft = self.pos
        self.discard_pile_anchor = ENEMY_DISCARD_ANCHOR
        self.captive_pile_anchor = ENEMY_CAPTIVE_ANCHOR
        self.color=DARKRED
        self.same_init(COL_NUM-2)

    def same_init(self,col):
        # 牌组、手牌初始化
        self.hand_cards_init()
        # 营地
        self.general_card = Proto_Card(self.game, self, self.card)
        self.general_card.direct_deploy(self.game.tile_list[col - self.front_speed][ROW_NUM // 2])
        self.general_card.become_general()
        self.camp = Proto_Card(self.game, self, self.game.cards_data_dc['Campsite'])
        self.camp.direct_deploy(self.game.tile_list[col][ROW_NUM // 2])
        self.camp.power, self.camp.power_max = 99, 99
        cnt = 0
        for step in Property.SurroundGrid8:
            x, y = self.camp.ipos[0] + step[0], self.camp.ipos[1] + step[1]
            if BasicTool.ipos_in_board((x, y)) and not self.game.tile_list[x][y].standing_card:
                guardcard = Proto_Card(self.game, self, self.game.cards_data_dc[CAMP_NEWMAN_DC[self.card_info['camp']]])
                guardcard.direct_deploy(self.game.tile_list[x][y])
                cnt += 1
            if cnt >= 5: break

    def get_enemy(self):
        if self.is_player:
            return self.game.rival
        else:
            return self.game.player

    def get_enemy_role(self):
        if self.is_player:
            return 'rival'
        else:
            return 'player'

    def image_init(self):
        self.image_orig = self.game.icon_images['card_front'].copy()
        self.rect = self.image_orig.get_rect()
        draw_text(self.image_orig,self.card_info['cn_name'], self.game.title_font, 14, BLACK, 5, self.rect.height // 8, 'nw')

        self.image=self.image_orig.copy()
        self.pos = vec(-100, -100)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos

    def turn_pass(self):
        self.game.outturn_role=self.role
        self.inturn = False
        self.maintain_dinars=len(self.captive_pile)
        # 己方场上的卡牌也开始回合结束后变化
        for card in self.game.cards.sprites():
            if card.loc_info == 'inboard' and card.owner.role == self.role:
                card.turn_pass()
                self.maintain_dinars+=1
        self.dinars+=self.turn_dinars-self.maintain_dinars


    def turn_begin(self):
        self.game.inturn_role = self.role
        self.inturn = True
        self.turns_num += 1
        self.turn_begin_time = pg.time.get_ticks()
        self.pick_hand_cards()
        self.turn_dinars = TURN_DINARS
        #己方场上的卡牌也开始回合前变化
        for card in self.game.cards.sprites():
            if card.loc_info=='inboard' and card.owner.role==self.role:
                card.turn_begin()
        #AI获取敌情
        #敌军最前线
        self.enemy_frontier=3
        self.enemy_adjacent_deploy_area=set()#敌方邻近可部署区域
        for i in range(4,COL_NUM):
            for j in range(ROW_NUM):
                tile=self.game.tile_list[i][j]
                if tile.standing_card and tile.standing_card.owner.role!=self.role:
                    self.enemy_frontier=max(self.enemy_frontier,i)
                    for step in [[1,0],[0,1],[0,-1]]:
                        self.enemy_adjacent_deploy_area.add((i+step[0],j+step[1]))
        #可部署的最前线
        self.deployable_farthest_frontier=min(COL_NUM-3,self.enemy_frontier)

    def update(self):
        if self.general_card:
            self.power=self.general_card.power
        self.image = self.image_orig.copy()
        # 手牌区画出卡牌
        self.draw_hand_cards()

    def draw_hand_cards(self):
        if self.inturn and (not self.game.single_player or self.is_player):
            for i in range(self.hand_cards_num()):
                self.hand_cards[i].set_pos((HAND_CARDS_ANCHOR[0]+i*TILE_WIDTH,HAND_CARDS_ANCHOR[1]))
        else:
            for i in range(self.hand_cards_num()):
                self.hand_cards[i].set_pos((-200,-200))

    def get_orders(self,pos):
        pass

    def hand_cards_init(self):
        self.deck_init()
        while self.hand_cards_num() < self._hand_cards_init_max:
            self.pick_hand_cards(1)

    def deck_init(self):
        arm_deck,tactic_deck=[],[]
        deck_id=self.game.cards_data[0].index(self.card_info['camp'])
        for card in self.game.cards_data[1:]:
            if card[deck_id]!='':
                for i in range(int(card[deck_id])):
                    if card[2] in ['building','tactic']:tactic_deck.append(card)
                    else:arm_deck.append(card)
        random.shuffle(arm_deck)
        random.shuffle(tactic_deck)
        self.deck=arm_deck+tactic_deck

    def hand_cards_num(self):
        return len(self.hand_cards)

    def computer_act(self):
        card=self.game.all_read_cards_dc[self.game.selected_card_uid]
        # 初始状态，先选中手牌，手牌都不能出，开始选中场上的牌
        if card.loc_info=='default':#选中的是占位卡
            for cd in self.hand_cards:
                if cd.card_info['level'] <= self.dinars:
                    cd.get_selected()
                    return
            #手牌都不能出，开始选中场上的牌
            self.get_computer_opt_cards()
            self.computer_choose_board_card()
            return
        #部署卡牌
        elif card.loc_info=='inhand':
            if card.accessible_tile_set:
                tmp_tiles = list(card.accessible_tile_set)
                if card.card_info['armbranch'] not in ['archer']:
                    # 近战先尝试部署在敌军周围
                    for ti in card.accessible_tile_set:
                        if ti in self.enemy_adjacent_deploy_area:
                            card.deploy(self.game.tile_list[ti[0]][ti[1]])
                            self.game.pre_selected_card.get_selected()
                            return
                    #否则部署在最前线
                    tmp_tiles.sort(key=lambda x:x[0]*10+random.randint(0,4))
                    card.deploy(self.game.tile_list[tmp_tiles[0][0]][tmp_tiles[0][1]])
                    self.game.pre_selected_card.get_selected()
                    return
                else:#远程部署在敌方前线后两排
                    tmp_tiles.sort(key=lambda x:x[0] + random.randint(0,4) if abs(x[0]-self.enemy_frontier)>=2 else x[0]*10+random.randint(0,4))
                    card.deploy(self.game.tile_list[tmp_tiles[0][0]][tmp_tiles[0][1]])
                    self.game.pre_selected_card.get_selected()
                    return
            elif card.attackable_tile_set:
                tmp_tiles = list(card.attackable_tile_set)
                card.tactic_affect(self.game.tile_list[tmp_tiles[0][0]][tmp_tiles[0][1]],int(card.vol_list[0]))
                return
            else:
                # 无地可部署，重新选择场上的牌
                self.get_computer_opt_cards()
                self.computer_choose_board_card()
        #场上卡牌移动
        elif card.loc_info == 'inboard':
            # 有主动技能时放技能
            for k, btn in self.game.buttons.items():
                if card.footpoint > 0 and btn.is_skill and btn.pos == btn.pos_orig:
                    btn.get_order()
            # 将军无法攻击时后退
            if card.is_general:
                # 将军血量充沛时攻击
                if card.power>=self.power_max*0.7 and len(card.attackable_tile_set) != 0:
                    random_ti = random.choice(list(card.attackable_tile_set))
                    card.attack(self.game.tile_list[random_ti[0]][random_ti[1]])
                    return
                elif 2<=card.ipos[0]<=COL_NUM-3:#已经出去了就后退
                    card.get_tactic_effect(['Withdraw'])
                    card.get_selected()
                elif card.accessible_tile_set and card.footpoint>0:
                    nextpos = random.choice(list(card.accessible_tile_set))  # 路走不通，随机走位
                    card.footpoint = 0
                    if nextpos not in card.attackable_tile_set:
                        card.set_tile_pos(self.game.tile_list[nextpos[0]][nextpos[1]])
                else:card.footpoint = 0
            # 非将军牌攻击
            if ((card.footpoint>0 and not card.is_general) or (card.footpoint==0 and card.card_info['armbranch']=='building')) and card.attackable_tile_set:
                random_ti = random.choice(list(card.attackable_tile_set))
                card.attack(self.game.tile_list[random_ti[0]][random_ti[1]])
            # 随机牌移动
            if card.accessible_tile_set and card.footpoint>0:#朝着敌军将领行进
                mpos = self.get_enemy().general_card.ipos
                path=AStar(self.game.map2d,Point(*card.ipos),Point(*mpos)).get_path()[::-1]
                #print(card.name,path)
                nextpos=0
                for pt in path:
                    if pt in card.accessible_tile_set:
                        nextpos=pt
                        break
                if not nextpos:#路走不通，随机走位
                    acclist = list(card.accessible_tile_set)
                    random.shuffle(acclist)
                    acclist.sort(key=lambda x: abs(mpos[0] - x[0]) + abs(mpos[1] - x[1]))
                    nextpos = random.choice(acclist[:3])
                card.footpoint = 0
                card.set_tile_pos(self.game.tile_list[nextpos[0]][nextpos[1]])
            else:# 不能行动，重新选择场上的牌
                self.get_computer_opt_cards()
                self.computer_choose_board_card()
            return

    def get_computer_opt_cards(self):
        self.computer_opt_cards = []
        for cd in self.game.cards.sprites():
            if cd.owner.role == self.role and cd.loc_info == 'inboard' and ((cd.footpoint>0 and (cd.accessible_tile_set or cd.attackable_tile_set)) or (cd.attack_times>0 and cd.attackable_tile_set)):
                self.computer_opt_cards.append(cd.uid)

    def computer_choose_board_card(self):
        if self.computer_opt_cards:
            random_cd = random.choice(self.computer_opt_cards)
            self.computer_opt_cards.remove(random_cd)
            self.game.all_read_cards_dc[random_cd].get_selected()
        else:
            # 回合结束
            self.game.game_turn_pass()

    def pick_hand_cards(self, add_num=2):
        #self.act_trigger('draw_card')
        count = 0
        tmpstr=''
        while count < int(add_num):
            if not self.deck:
                tmpstr+="%s牌堆已空，" % self.title
                break
            elif len(self.hand_cards) == self._hand_cards_max:
                tmpstr+="%s达到手牌上限，" % self.title
                break
            else:
                if random.random()<=0.9:
                    computer_choice = self.deck.pop(0)#牌堆初始化时已经打乱了，这里按顺序
                else:
                    computer_choice = self.deck.pop()
                card=Proto_Card(self.game,self,computer_choice)
                self.hand_cards_append(card)
                descripts=card.card_info['cn_name']
                if not self.is_player: descripts = "不可见"
                tmpstr+="%s获得了新卡牌:" % self.title +descripts + " ,"
                count += 1
        self.game.add_log(tmpstr+"总共获得了%d张卡牌。" % count)

    def gain_hand_cards(self, card=None):
        if card != None:
            if len(self.hand_cards) == self._hand_cards_max:
                self.game.add_log("%s达到手牌上限，" % self.title)
                card.get_discarded()#卡牌销毁
            else:
                card.owner=self #修改主人
                card.add(self.game.all_sprites,self.game.cards)#获得卡牌，可能获得从弃牌堆和俘虏堆来的牌，要添加到all_sprites和cards中
                self.hand_cards_append(card)
                self.game.add_log("%s获得了新卡牌:%s" %(self.title,card.card_info['cn_name'] ))

    def hand_cards_append(self,card):
        self.hand_cards.append(card)
        card.change_loc_info('inhand')

    def discard_pile_append(self,card):#弃牌回收内存
        self.discard_pile.append(card.name)
        card.kill()
        del self.game.all_read_cards_dc[card.uid]
        gc.collect()

    def captive_pile_append(self,card):#俘虏只收uid
        self.captive_pile.append(card.uid)
        card.change_loc_info('captured')
        card.set_pos(self.captive_pile_anchor)
        card.kill()

    def get_captive_summery(self):
        cap_dc={}
        for cap_uid in self.captive_pile:
            cap_name=self.game.all_read_cards_dc[cap_uid].card_info['cn_name']
            if cap_name in cap_dc.keys():cap_dc[cap_name] += 1
            else:cap_dc[cap_name]=1
        cap_texts=[name+'x%d'%num for name,num in cap_dc.items()]
        self.captive_summery_image = self.game.icon_images['card_front'].copy()
        draw_text(self.captive_summery_image,'俘虏%d'%(len(self.captive_pile)), self.game.title_font, 14, BLACK, TILE_WIDTH//2, 12, 'center')
        for i in range(len(cap_texts)):
            draw_text(self.captive_summery_image, cap_texts[i], self.game.title_font, 10, BLACK, 5,self.rect.height * (i +2) // 10, 'nw')
        return self.captive_summery_image

    def pop_hand_cards(self, i):
        if not self.hand_cards:
            self.game.add_log("%s手牌已空。" % self.title)
        else:
            pop_card = self.hand_cards.pop(i)
            self.discard_pile_append(pop_card)
            return pop_card

    #拆手牌，随机拆
    def drop_hand_cards(self, drop_num=1):
        count = 0
        tmpstr=''
        while count < int(drop_num):
            if not self.hand_cards:
                tmpstr+="%s手牌已空," % self.title
                break
            else:
                card_idx=random.randint(0,len(self.hand_cards)-1)
                computer_choice = self.hand_cards.pop(card_idx)
                self.discard_pile_append(computer_choice )
                tmpstr+="%s失去了卡牌:" % self.title + computer_choice.card_info['cn_name'] +" ,"
                count += 1
        self.game.add_log(tmpstr+"总共失去了%d张卡牌。" % count)




