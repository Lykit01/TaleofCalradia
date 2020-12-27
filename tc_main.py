#!/usr/bin/env python
# -*- coding:utf-8 -*-
from tc_creatures import *

class Game:
    def __init__(self):
        global pg
        pg.init()
        pg.mixer.init()
        self.dir = os.path.dirname(__file__)
        self.img_dir = os.path.join(self.dir,'img')
        self.snd_dir = os.path.join(self.dir,'snd')
        self.screen = pg.display.set_mode(SIZE)
        pg.display.set_caption(TITLE)
        icon=pg.image.load(os.path.join(self.img_dir,'icon.png'))
        icon.set_colorkey(WHITE)
        pg.display.set_icon(icon)
        self.clock=pg.time.Clock()
        self.running=True
        self.pause=False
        self.font_name=pg.font.match_font(FONT_NAME)

        self.load_data()

    def load_data(self):
        # screen
        self.dim_screen = pg.Surface(self.screen.get_size()).convert_alpha()
        self.dim_screen.fill((0, 0, 0, 180))

        # load high score
        with open(os.path.join(self.dir, HS_FILE), 'w') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

        # img_dir
        self.img_dir_dict = {x: os.path.join(self.img_dir, x) for x in ["backgrounds"]}

        # background images
        self.background_images = []
        for root, dirs, files in os.walk(self.img_dir_dict["backgrounds"]):
            filenames = files
        bg_reg = re.compile('bg[0-9]+\.png')
        for name in filenames:
            if bg_reg.match(name):
                img = pg.image.load(os.path.join(self.img_dir_dict["backgrounds"], name)).convert()
                self.background_images.append(pg.transform.scale(img, BG_SIZE))

        #spritesheet
        self.spritesheet_neutral=SpriteSheet(self,'spritesheet_neutral')#这里不要带png
        self.spritesheet_unit={}
        self.spritesheet_unit['player'] = SpriteSheet(self, 'spritesheet_player')
        self.spritesheet_unit['rival'] = SpriteSheet(self, 'spritesheet_rival')
        self.icon_images = {}#常用图像直接读出来
        for icon in ['tile_accessible','tile_attackable','tile_selected']:
            self.icon_images[icon]=pg.transform.scale(self.spritesheet_neutral.get_image_fn(icon),(GRID_DIAM,GRID_DIAM))
        for icon in ['card_front', 'card_selected']:
            self.icon_images[icon] = pg.transform.scale(self.spritesheet_neutral.get_image_fn(icon),(TILE_WIDTH,TILE_HEIGHT))
        #正面朝向
        self.icon_images['face_left']=pg.transform.scale(self.spritesheet_neutral.get_image_fn('face_left'),(SMALL_DIAM,SMALL_DIAM))
        self.icon_images['face_right']=pg.transform.rotate(self.icon_images['face_left'],180)
        self.icon_images['face_up']=pg.transform.rotate(self.icon_images['face_left'],270)
        self.icon_images['face_down']=pg.transform.rotate(self.icon_images['face_left'],90)

        # cards
        self.cards_data = []
        self.cards_data_dc={}
        with open(os.path.join(self.dir, CARD_FILE), 'r') as f:
            rawd = csv.reader(f)
            for row in rawd:
                self.cards_data.append(row)
                self.cards_data_dc[row[1]]=row
        #skills_data
        self.skills_data = []
        self.skills_data_dc={}
        with open(os.path.join(self.dir, SKILL_FILE), 'r') as f:
            rawd = csv.reader(f)
            for row in rawd:
                self.skills_data.append(row)
                if row[0]!='number':self.skills_data_dc[row[1]]=Skill(self,row)
        # items_data
        self.items_data = []
        self.items_data_dc = {}
        with open(os.path.join(self.dir, ITEM_FILE), 'r') as f:
            rawd = csv.reader(f)
            for row in rawd:
                self.items_data.append(row)
                if row[0] != 'number': self.items_data_dc[row[1]] = Item(self, row)

        # font
        self.title_font = os.path.join(self.img_dir, 'pingfangblack-thin-simplified.ttf')

    def new(self):
        # sprite group
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.cards = pg.sprite.LayeredUpdates()
        self.tiles = pg.sprite.LayeredUpdates()
        self.backgrounds = pg.sprite.LayeredUpdates()
        self.pows = pg.sprite.LayeredUpdates()

        # init surface element
        Background(self, 0, 0)
        Background(self, 0, -HEIGHT)

        #提前选择地格
        self.pre_selected_tile=Tile(self,-200,-200)
        self.pre_selected_tile.selected=True
        self.selected_tile=self.pre_selected_tile

        #提前选择卡片
        self.uid_cnt=0
        self.pre_char=Creature(self, 'Chief Ukes')
        self.all_read_cards_dc={}
        self.pre_selected_card=Proto_Card(self,self.pre_char,self.cards_data_dc['Preselected'])
        self.pre_selected_card.selected=True
        self.selected_card_uid=self.pre_selected_card.uid

        #单人或双人模式
        self.single_player=True
        self.two_computers=False

        # UI
        self.buttons={}
        self.buttons['next_turn']=Button(self,'next_turn',NEXT_TURN_BUTTON_ANCHOR)
        self.buttons['restart_game'] = Button(self, 'restart_game', (NEXT_TURN_BUTTON_ANCHOR[0]+BUTTON_DIAM*3,NEXT_TURN_BUTTON_ANCHOR[1]))
        self.buttons['Heal'] = Askill_Button(self, 'Heal', [SKILL_BUTTON_ANCHOR[0],SKILL_BUTTON_ANCHOR[1]+BUTTON_DIAM])
        self.buttons['Retreat'] = Askill_Button(self, 'Retreat',[SKILL_BUTTON_ANCHOR[0], SKILL_BUTTON_ANCHOR[1] + BUTTON_DIAM])
        self.buttons['BuildCamp'] = Askill_Button(self, 'BuildCamp',[SKILL_BUTTON_ANCHOR[0]+BUTTON_DIAM, SKILL_BUTTON_ANCHOR[1] + BUTTON_DIAM])
        self.buttons['VillageRecruit'] = Askill_Button(self, 'VillageRecruit',[SKILL_BUTTON_ANCHOR[0], SKILL_BUTTON_ANCHOR[1] + 2*BUTTON_DIAM])
        self.buttons['Tax'] = Askill_Button(self, 'Tax', [SKILL_BUTTON_ANCHOR[0]+BUTTON_DIAM,SKILL_BUTTON_ANCHOR[1] + 2 * BUTTON_DIAM])
        self.buttons['GrainLevies'] = Askill_Button(self, 'GrainLevies', [SKILL_BUTTON_ANCHOR[0] + 2*BUTTON_DIAM,SKILL_BUTTON_ANCHOR[1] + 2 * BUTTON_DIAM])
        self.buttons['SellingCaptives'] = Askill_Button(self, 'SellingCaptives', [SKILL_BUTTON_ANCHOR[0],SKILL_BUTTON_ANCHOR[1] + 3 * BUTTON_DIAM])
        self.buttons['CallonEnemy'] = Askill_Button(self, 'CallonEnemy', [SKILL_BUTTON_ANCHOR[0]+BUTTON_DIAM,SKILL_BUTTON_ANCHOR[1] + 3 * BUTTON_DIAM])
        #晋升按钮
        for i in range(3):
            self.buttons['button_upgrade%d'%i]=Upgrade_Button(self,'button_upgrade%d'%i,[SKILL_BUTTON_ANCHOR[0]+BUTTON_DIAM*i,SKILL_BUTTON_ANCHOR[1]])
        self.turn_explain_words = ['此处是文字说明框。'] + [''] * (TURN_EXPLAIN_NUM-1)

        #双方角色'Earl Frad':2,'Lord Casto':3,'Khan Saiga':4,'Prince Vidim':5,'Prophet Levine':6,'Chief Ukes':7
        self.inturn_role='player'
        self.outturn_role='rival'
        self.player =Creature(self, 'Earl Frad')
        self.rival =Creature(self, 'Prophet Levine')
        #根据交战双方生成地形
        self.generate_battlefield()
        #双方角色准备
        self.player.become_player()
        self.player.turn_begin()
        self.rival.become_player_rival()
        #others
        self.turns_num=1
        self.turns_role_txt=self.player.title+'回合'
        self.result='equal'
        self.score=0

        #实验用卡
        # self.testcard1 = Proto_Card(self, self.player, self.cards_data[51])
        # self.testcard1.direct_deploy(self.tile_list[1][0])
        # self.testcard1.turn_pass()
        # self.testcard1.exp=5
        # self.testcard2 = Proto_Card(self, self.rival, self.cards_data[33])
        # self.testcard2.direct_deploy(self.tile_list[2][2])
        # self.testcard2.turn_pass()

        self.to_hover = False
        self.continue_card_uid=''
        self.mpos=(-100,-100)

        #game loop
        self.run()

    def generate_battlefield(self):
        n1,n2,n3=3*ROW_NUM//4,3*ROW_NUM//6,3*ROW_NUM//10
        n4=3*ROW_NUM-n1-n2-n3-9
        player_terrains=[CAMP_LINK_TERRAIN_DC[self.player.card_info['camp']]]*n1+['plain']*n2+['village']*n3 +[random.choice(TILE_TERRAINS+['mount']) for _ in range(n4)]
        random.shuffle(player_terrains)
        rival_terrains = [CAMP_LINK_TERRAIN_DC[self.rival.card_info['camp']]]*n1+['plain']*n2+['village']*n3 +[random.choice(TILE_TERRAINS + ['mount']) for _ in range(n4)]
        random.shuffle(rival_terrains)
        allnum=(COL_NUM-6)*ROW_NUM
        mount_num=random.randint(allnum//10,allnum*2//10)
        n1,n2,n3=allnum*3//10,allnum//10,allnum//10
        n4=allnum-n1-n2-n3-mount_num
        middle_terrains =[random.choice(TILE_TERRAINS)] *n3 +[random.choice(TILE_TERRAINS) for _ in range(n4)]+ ['mount']*mount_num+ ['plain']*n1+['village']*n2
        random.shuffle(middle_terrains)

        self.map2d = Array2D(COL_NUM, ROW_NUM)
        self.tile_list = [[0] * ROW_NUM for _ in range(COL_NUM)]
        for i in range(COL_NUM):
            for j in range(ROW_NUM):
                if i in (1,COL_NUM-2) and j==ROW_NUM//2:
                    terrain = 'plain'#初始营地一定是平原
                elif i<=2 and ROW_NUM//2-1<=j<=ROW_NUM//2+1:
                    terrain=random.choice([CAMP_LINK_TERRAIN_DC[self.player.card_info['camp']],'plain'])#营地周围是目标地形和平原的随机
                elif i>=COL_NUM-3 and ROW_NUM//2-1<=j<=ROW_NUM//2+1:
                    terrain = random.choice([CAMP_LINK_TERRAIN_DC[self.rival.card_info['camp']], 'plain'])
                elif i <= 2:  # 玩家地形，目标地形7，基本地形5，随机地形3，基本地形：平原
                    terrain = player_terrains.pop()
                elif i>=COL_NUM-3:  # 对手地形，目标地形7，基本地形5，随机地形3，基本地形：平原
                    terrain = rival_terrains.pop()
                else:# 中间地形，目标随机地形4，基本地形5，随机地形1，基本地形：平原
                    terrain = middle_terrains.pop()
                tile = Tile(self, TILE_ANCHOR[0] + i * (GRID_DIAM + TILE_GAP),TILE_ANCHOR[1] + j * (GRID_DIAM + TILE_GAP), terrain)
                tile.ipos = (i, j)
                self.tile_list[i][j] = tile
                if terrain=='mount':self.map2d[i][j]=1


    def run(self):
        # game loop
        # pg.mixer.music.play(loops=-1)
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()  # 暂停、离开等宏观操作
            if not self.pause:
                self.update()  # 游戏逻辑
            self.draw()  # 画面展现,这个要移动到每次行动中
        # pg.mixer.music.fadeout(500)

    def update(self):
        # game loop update
        self.all_sprites.update()
        #游戏结束判定
        if self.player.power<=0 and self.rival.power<=0:
            self.playing = False
        elif self.player.power<=0:
            self.result='playerlose'
            self.score = -self.rival.power-max(0,self.turns_num-10)
            self.playing = False
        elif self.rival.power<=0:
            self.result = 'playerwin'
            self.score = self.player.power - max(0,self.turns_num-10)
            self.playing = False


    def events(self):
        # game loop events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_p:
                    self.pause = not self.pause
                if event.key == pg.K_g:
                    self.playing=False
                if event.key == pg.K_t:#回合更替
                    if self.player.inturn or (not self.single_player and self.rival.inturn):
                        self.game_turn_pass()
                if event.key == pg.K_c:#debug
                    print(self.all_read_cards_dc[self.selected_card_uid].card_info['cn_name'],'将领',self.all_read_cards_dc[self.selected_card_uid].owner.card_info['cn_name'])
                    print(len(self.all_read_cards_dc),len(self.cards))
                    for k,v in self.all_read_cards_dc.items():
                        if v not in self.cards:
                            print(k,v.name)
                    #if self.tile_list[0][2].standing_card:print(self.tile_list[0][2].standing_card.uid)
                    # if self.tile_list[2][2].standing_card:print(self.tile_list[2][2].standing_card.uid)
            #监测鼠标
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                if self.player.inturn or (not self.single_player and self.rival.inturn):#双人游戏时也接收键盘指令
                    for ti in self.tiles.sprites():
                        if ti.isclick(event.pos):
                            ti.get_order()
                    for cd in self.cards.sprites():
                        if cd.isclick(event.pos):
                            cd.get_order()
                    for n,b in self.buttons.items():
                        if b.isclick(event.pos):
                            b.get_order()
        self.hover_show()#悬停鼠标看详情
        #AI操作游戏
        if self.single_player and self.rival.inturn:
            now=pg.time.get_ticks()
            if now-self.rival.turn_begin_time>500:
                self.rival.turn_begin_time=now
                self.rival.computer_act()
        if self.two_computers and self.player.inturn:
            now = pg.time.get_ticks()
            if now - self.player.turn_begin_time > 500:
                self.player.turn_begin_time = now
                self.player.computer_act()

    def hover_show(self):
        self.mpos = pg.mouse.get_pos()
        checked=False
        for cd in self.cards.sprites():
            if cd.isclick(self.mpos) and not cd.selected and cd.loc_info=='inboard':
                checked=True
                if cd.uid==self.continue_card_uid:
                    self.to_hover_cnt+=1
                else:
                    self.to_hover_cnt=1
                    self.continue_card_uid=cd.uid
                if self.to_hover_cnt>=8:
                    self.to_hover = True
                    self.to_hover_card_uid=cd.uid
                else:
                    self.to_hover=False
        if not checked:self.to_hover=False

    # 回合更替
    def game_turn_pass(self):
        self.pre_selected_card.get_selected()
        if self.player.inturn:
            self.player.turn_pass()
            self.turns_role_txt = self.rival.title + '回合'
            self.rival.turn_begin()
        else:
            self.rival.turn_pass()
            self.turns_role_txt = self.player.title + '回合'
            self.player.turn_begin()
        self.turns_num=max(self.player.turns_num,self.rival.turns_num)
        #tile每回合更新
        for i in range(COL_NUM):
            for j in range(ROW_NUM):
                tile=self.tile_list[i][j]
                for cond in tile.tile_cond[self.outturn_role].keys():
                    #这回合结束的角色的状态-1
                    tile.tile_cond[self.outturn_role][cond]=max(0,tile.tile_cond[self.outturn_role][cond]-1)
                #村庄产出第纳尔
                if tile.terrain=='village' and tile.tile_cond[self.inturn_role]['camp'] and not tile.tile_cond[self.inturn_role]['watched']:
                    if self.player.inturn:self.player.turn_dinars+=3
                    else:self.rival.turn_dinars += 3

    # 游戏界面
    def draw(self):
        # game loop draw
        self.screen.fill(BGCOLOR)
        for bg in self.backgrounds:
            self.screen.blit(bg.image, (0, bg.rect.y))
        for sprite in self.all_sprites:#先画血条，再画精灵本身的图案
            if isinstance(sprite,Proto_Card) and sprite.loc_info=='inboard':
                sprite.draw_health()
                sprite.image.blit(self.icon_images[sprite.face_dir],Property.DIRPOS[sprite.face_dir])#卡牌的方向
            self.screen.blit(sprite.image,sprite.pos)
        # UI
        #self.all_sprites.draw(self.screen)  # plat can overlap player now
        #各种特效，如伤害、回复、闪避
        for pow in self.pows:
            draw_text(self.screen, pow.content, self.title_font, pow.font_size, pow.color,*pow.pos, 'center')
        #选中卡牌的详情
        if self.to_hover and self.to_hover_card_uid in self.all_read_cards_dc.keys():
            self.screen.blit(self.all_read_cards_dc[self.to_hover_card_uid].hover_image,self.all_read_cards_dc[self.to_hover_card_uid].rect.topright)
        if self.all_read_cards_dc[self.selected_card_uid].loc_info!='default':
            self.screen.blit(self.all_read_cards_dc[self.selected_card_uid].detail_image,CARD_DETAIL_ANCHOR)
        # grid
        draw_text(self.screen, '第纳尔：%d+%d-%d' % (self.player.dinars,self.player.turn_dinars,self.player.maintain_dinars), self.title_font, 12, WHITE,
                  PLAYER_GENERAL_ANCHOR[0]+TILE_WIDTH//2, PLAYER_GENERAL_ANCHOR[1]+TILE_HEIGHT+10, 'n')
        draw_text(self.screen, '手牌:%d 牌堆:%d 弃牌:%d' % (len(self.player.hand_cards),len(self.player.deck),len(self.player.discard_pile)), self.title_font, 12, WHITE,
                  PLAYER_GENERAL_ANCHOR[0] + TILE_WIDTH // 2, PLAYER_GENERAL_ANCHOR[1] + TILE_HEIGHT + 30,'n')
        draw_text(self.screen, '资源 马:%d' % (self.player.horse_stock), self.title_font, 12, WHITE,
                  PLAYER_GENERAL_ANCHOR[0] + TILE_WIDTH // 2, PLAYER_GENERAL_ANCHOR[1] + TILE_HEIGHT + 50, 'n')
        draw_text(self.screen, '第纳尔：%d+%d-%d' % (self.rival.dinars, self.rival.turn_dinars,self.rival.maintain_dinars), self.title_font, 12, WHITE,
                  ENEMY_GENERAL_ANCHOR[0]+TILE_WIDTH//2, ENEMY_GENERAL_ANCHOR[1] + TILE_HEIGHT + 10, 'n')
        draw_text(self.screen, '手牌:%d 牌堆:%d 弃牌:%d' % (len(self.rival.hand_cards), len(self.rival.deck),len(self.rival.discard_pile)), self.title_font,12, WHITE,
                  ENEMY_GENERAL_ANCHOR[0] + TILE_WIDTH // 2, ENEMY_GENERAL_ANCHOR[1] + TILE_HEIGHT + 30,'n')
        draw_text(self.screen, '资源 马:%d' % (self.rival.horse_stock), self.title_font, 12, WHITE,
                  ENEMY_GENERAL_ANCHOR[0] + TILE_WIDTH // 2, ENEMY_GENERAL_ANCHOR[1] + TILE_HEIGHT + 50, 'n')
        #俘虏
        self.screen.blit(self.player.get_captive_summery(),PLAYER_CAPTIVE_ANCHOR)
        self.screen.blit(self.rival.get_captive_summery(), ENEMY_CAPTIVE_ANCHOR)
        # 回合数标注
        draw_text(self.screen, '第 %d 回合: %s (按T结束)' % (self.turns_num,self.turns_role_txt), self.title_font, 20, WHITE, TURN_SIGN_ANCHOR[0], TURN_SIGN_ANCHOR[1], 'center')
        #回合说明
        for i in range(len(self.turn_explain_words)):
            draw_text(self.screen,self.turn_explain_words[i], self.title_font, 12, BLACK, EXPLAIN_BUCKET_POS[0],EXPLAIN_BUCKET_POS[1]+20*i, 'nw')

        # after drawing everything,flip the display
        pg.display.flip()

    def show_start_screen(self):
        # start screen
        # pg.mixer.music.load(os.path.join(self.snd_dir,'Yippee.ogg'))
        # pg.mixer.music.play(loops=-1)
        self.screen.blit(random.choice(self.background_images), (0, 0))
        anx, anky = WIDTH // 12, HEIGHT // 2
        draw_text(self.screen, TITLE, self.title_font, 48, BLACK, anx, anky, 'nw')
        draw_text(self.screen, '按任意键开始游戏', self.title_font, 22, BLACK, anx, anky + 80, 'nw')
        draw_text(self.screen, '历史最高分:%d' % self.highscore, self.title_font, 22, BLACK, anx, anky + 120, 'nw')
        draw_text(self.screen, '按H获得帮助', self.title_font, 22, BLACK, anx, anky + 160, 'nw')
        draw_text(self.screen, '@Hue Zhang', self.title_font, 14, BLACK, anx, HEIGHT - 50, 'nw')
        pg.display.flip()
        self.wait_for_key()
        # pg.mixer.music.fadeout(500)

    def show_go_screen(self):
        # game over
        if not self.running:
            return
        # pg.mixer.music.load(os.path.join(self.snd_dir, 'Yippee.ogg'))
        # pg.mixer.music.play(loops=-1)
        # self.screen.blit(random.choice(self.background_images),(0,0))
        if self.result=='equal':
            color=BLACK
            text='平局'
        elif self.result=='playerlose':
            color=RED
            text='你输了'
        elif self.result=='playerwin':
            color=BLUE
            text = '你赢了'
        draw_text(self.screen,  '%s 得分：%d' % (text,self.score), self.title_font, 48, color, WIDTH // 2, HEIGHT // 5)
        draw_text(self.screen, '点击任意位置继续游戏', self.title_font, 22, color, WIDTH // 2, HEIGHT * 2 // 5)
        draw_text(self.screen, '@Hue Zhang', self.title_font, 14, color, WIDTH // 2, HEIGHT * 3 // 5)
        if self.score > self.highscore:
            self.highscore = self.score
            draw_text(self.screen, '新记录!', self.title_font, 22, color, WIDTH // 2, HEIGHT * 2 // 5 + 40)
            with open(os.path.join(self.dir, HS_FILE), 'w') as f:
                f.write(str(self.highscore))
        else:
            draw_text(self.screen, '最高分:%d' % self.highscore, self.title_font, 22, color, WIDTH // 2,HEIGHT * 2 // 5 + 40)
        pg.display.flip()
        self.wait_for_key()
        # pg.mixer.music.fadeout(500)

    def wait_for_key(self):
        pg.event.wait()  # 重新载入事件队列。没有这一句的话，上一局游戏中未执行的按键也会触发重新开始游戏
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Waiting = False
                    self.quit()
                if event.type == pg.KEYUP:
                    waiting = False
                if event.type == pg.KEYDOWN:
                    waiting = False
                # 监测鼠标
                if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                    waiting = False

    def add_log(self,text):
        if text:
            texts = BasicTool.cut_text(text,18)
            self.turn_explain_words=self.turn_explain_words[len(texts):]+texts

    def quit(self):
        pg.quit()
        sys.exit()

g = Game()
g.show_start_screen()
while g.running:
    g.new()
    g.show_go_screen()

pg.quit()


