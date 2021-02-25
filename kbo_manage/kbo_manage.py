#%% 팀 정보를 저장할 클래스
class Team:
    def __init__(self, team_name,season, win, lose):
        self.team_name = team_name
        self.season = season
        self.win = win
        self.lose = lose

    def __str__(self):
        return "{}시즌 {}팀은 {}승 {}패, 승률은 {:2}입니다. (잔여경기: {})"\
            .format(self.season, self.team_name, self.win, self.lose, (self.win)/(self.win+self.lose), 144-(self.win+self.lose))

#%% 경기 정보를 저장할 클래스
class Game:
    def __init__(self, home_team, away_team, game_date, home_score, away_score, stadium, season):
        self.home_team = home_team 
        self.away_team  = away_team
        self.game_date  = game_date
        self.home_score  = home_score
        self.away_score  = away_score
        self.stadium = stadium
        self.season = season
    
    def __str__(self):
        return "{} vs {} ({} 구장)"\
            .format(self.home_team, self.away_team, self.stadium)
    
    def to_dict(self):
        return {"season":self.season, "home_team":self.home_team, "away_team":self.away_team, "game_date":self.game_date,\
                    "home_score":self.home_score, "away_scroe":self.away_score, "stadium":self.stadium}
#%% 경기 정보를 저장하는 메소드
def insert_game_info():
    cursor = conn.cursor()
    
    season = input("시즌: ")
    home_team = input("홈팀: ")
    away_team = input("원정팀: ")
    game_date = input("경기날짜와 시간(ex)2020-02-27 18:30): ")
    pattern = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    
    if re.fullmatch(pattern, game_date) == None:
        print('잘못된 입력값 입니다.')
        return
    
    home_score = int(input("홈팀 점수: "))
    away_score = int(input("원정팀 점수: "))
    stadium = input("경기장: ")
    
    sql = """insert into games(home_team, away_team, game_date, home_score, away_score, stadium, season)
values(:1, :2, to_date(:3, 'YYYY-MM-DD HH24:MI'), :4, :5, :6, :7)"""
    
    sql_win = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.win = a.win+1
                when not matched then
                    insert values(:1, :2, 1, 0, 0)"""
                    
    sql_lose = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.lose = a.lose+1
                when not matched then
                    insert values(:1, :2, 0, 1, 0)"""
                
    sql_draw = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.draw = a.draw+1
                when not matched then
                    insert values(:1, :2, 0, 0, 1)"""
                    
    try:
        cursor.execute(sql, (home_team, away_team, game_date, home_score, away_score, stadium, season))
    except:
        print('경기 정보 입력에 실패했습니다.')
        return
    
    if home_score > away_score:
        cursor.execute(sql_win, (season, home_team))
        cursor.execute(sql_lose, (season,away_team))
    elif home_score < away_score:
        cursor.execute(sql_lose, (season, home_team))
        cursor.execute(sql_win, (season, away_team))
    else:
        cursor.execute(sql_draw, (season, home_team))
        cursor.execute(sql_draw, (season, away_team))
        
#%% 경기 파일을 입력받아 데이터베이스에 저장
def insert_game_season(season):
    file_name = "KBO_"+season+"_season.csv"
    cursor = conn.cursor()
    sql1 = """insert into games(home_team, away_team, game_date, home_score, away_score, stadium, season)
                            values(:1, :2, to_date(:3, 'YYYY-MM-DD HH24:MI'), :4, :5, :6, :7)"""
    
    sql_win = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.win = a.win+1
                when not matched then
                    insert values(:1, :2, 1, 0, 0)"""
                    
    sql_lose = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.lose = a.lose+1
                when not matched then
                    insert values(:1, :2, 0, 1, 0)"""
                
    sql_draw = """merge into season_record a
                using dual
                    on (a.season = :1 and a.team_name = :2)
                when matched then
                    update set
                        a.draw = a.draw+1
                when not matched then
                    insert values(:1, :2, 0, 0, 1)"""
    
    with open(file_name, encoding='UTF8') as f:
        dict_reader = csv.DictReader(f)
        for row in dict_reader:
            if row["비고"] == "정규시즌":
                cursor.execute(sql1, (row["홈팀"], row["원정팀"], row["Date"], row["홈팀점수"], row["원정팀점수"], row["구장"], season))
                
                if row["홈팀결과"] == "승":
                    cursor.execute(sql_win, (season, row["홈팀"]))
                    cursor.execute(sql_lose, (season, row["원정팀"]))
                elif row["홈팀결과"] == "패":
                    cursor.execute(sql_lose, (season, row["홈팀"]))
                    cursor.execute(sql_win, (season, row["원정팀"]))
                elif row["홈팀결과"] == "무":
                    cursor.execute(sql_draw, (season, row["홈팀"]))
                    cursor.execute(sql_draw, (season, row["원정팀"]))

#%% 해당 날자의 경기들을 보여줌 (1. 해당날자 입력->경기들 -> 2. 경기선택 -> 3.해당 경기 결과)
def select_game(game_date):
    cursor = conn.cursor()
    pattern = '(\d{4}-\d{2}-\d{2})'
    
    if re.fullmatch(pattern, game_date) == None:
        print('잘못된 입력값 입니다.')
        return
    
    try:
        sql = "select * from games where to_char(game_date,'YYYY-MM-DD')=:game_date"
        cursor.execute(sql,{"game_date":game_date})
    except:
        print('실패했습니다.')
        return
    
    game_list = []
    for data in cursor:
        game_list.append(Game(*data))
    
    if len(game_list) == 0:
        print('{:^55}'.format('해당 일자에는 경기가 없습니다.'))
        return
    
    print()
    print('{:^55}'.format('해당일의 경기들 입니다.'))
    print('{:=^65}'.format(''))
    for game in game_list:
        print(game)
    print('{:=^65}'.format(''))
    
    
    
    while True:
        stadium = input("결과를 알고 싶은 경기의 구장을 선택하세요: ")
        if stadium != '':
            break
        
    real_game = ""
    for game in game_list:
        if game.stadium == stadium:
            real_game = game
            break
        
    show_game_result(real_game)
    
#%% 데이터베이스에서 조회한 정보를 CSV파일로 저장하는 함수
def export_season_info():
    season = input("저장할 시즌을 입력해주세요.: ")
    file_name = "KBO_"+season+"_season_fake.csv"
    cursor = conn.cursor()
    sql = """
        select game_date, stadium, away_team, away_score, home_score, home_team
        from games
        where season=:1
        order by game_date asc
    """
    cursor.execute(sql,(season,))
    data = cursor.fetchall()
    colnames = ['Date', '구장', '원정팀', '원정팀점수','홈팀점수','홈팀','시즌']
    
    with open(file_name, 'w', newline='', encoding='UTF8') as file:
        w = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
        w.writerow(colnames)
        for row in data:
            row += (season,)
            w.writerow(row)
        
#%% 해당 경기의 결과를 보여
def show_game_result(real_game):
    print('{:-^60}'.format('경기 결과'))
    print()
    str_ = '{} vs {}'.format(real_game.home_team,real_game.away_team)
    print('{:^61}'.format(str_))
    print()
    str_ = '{} : {}'.format(real_game.home_score, real_game.away_score)
    print('{:^65}'.format(str_))
    print()
    home = real_game.home_score
    away = real_game.away_score
    if home > away:
        print("홈팀인 {}이(가) 승리했습니다.".format(real_game.home_team))
    elif home < away:
        print("원정팀인 {}이(가) 승리했습니다.".format(real_game.away_team))
    else:
        print("무승부가 났습니다.")
    print('{:-^60}'.format(''))
    
#%% 팀이름으로 팀 성적을 조회하는 함수
def get_team_record(team_name):
    real_team_name = ""
    cursor = conn.cursor()
    if team_name == 1: #한화 이글스
        real_team_name = "한화"
    elif team_name == 2: #두산 베어스
        real_team_name = "두산"
    elif team_name == 3: #롯데 자이언츠
        real_team_name = "롯데"
    elif team_name == 4: #삼성 라이온즈
        real_team_name = "삼성"
    elif team_name == 5: #넥센 히어로즈
        real_team_name = "넥센"
    elif team_name == 6: #SK 와이번스
        real_team_name = "SK"
    elif team_name == 7: #기아 타이거즈
        real_team_name = "기아"
    elif team_name == 8: #KT WIZ
        real_team_name = "KT"
    elif team_name == 9: #LG 트윈스
        real_team_name = "LG"
    elif team_name == 10: #NC 다이노스
        real_team_name = "NC"
    else:
        print('해당되는 팀이 없습니다.')
        return
    
    season = input("원하는 시즌을 입력하세요(2015~): ")
    sql = """
        select team_name, win, lose, draw,
            rank() over(order by (win)/(win+lose) desc) as rank
        from season_record
        where season =:season and (win+lose)>0"""
    sql_team_info = """
        select start_year, victory, sub_name
        from teams
        where team_name=:team_name
    """
    cursor.execute(sql, {"season":season})
    datas = cursor.fetchall()
    
    cursor.execute(sql_team_info, {"team_name":real_team_name})
    team_information = cursor.fetchone()
    
    if len(datas) == 0:
        print('해당 시즌의 데이터가 없습니다.')
        return
           
    print('{:=^65}'.format(''))
    print()
    str_ = ' {} {} '.format(season, real_team_name)
    print('{:=^65}'.format(str_))
    print()
    str_ = '{}년에 창단된 {} {}입니다! (Time to V{}!)'.format(team_information[0],real_team_name,team_information[2],team_information[1]+1)
    print('{:^55}'.format(str_))
    print()
    print('{:=^65}'.format(''))
    for data in datas:
        if data[0] == real_team_name:
            win = data[1]
            lose = data[2]
            draw = data[3]
            
            print("   승률 : {:0.4f}".format((win)/(win+lose)))
            print("   순위 :",data[4])
            if win + lose + draw == 144:
                print("   종료된 시즌입니다")
            else:
                print("   잔여 경기 : {} ".format(144-(win + lose + draw)))
            break;
        
    print('{:=^65}'.format(''))
#%% 경기 정보를 삭제하는 함수입니다.
def delete_game_info():    
    cursor = conn.cursor()
    
    home_team = input("홈팀: ")
    away_team = input("원정팀: ")
    game_date = input("경기날짜와 시간(ex)2020-02-27 18:30): ")
    pattern = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    
    if re.fullmatch(pattern, game_date) == None:
        print('잘못된 입력값 입니다.')
        return
    
    get_sql = """
        select home_team, away_team, home_score, away_score, season
        from games
        where home_team=:1 
            and away_team=:2 
            and to_char(game_date, 'YYYY-MM-DD HH24:MI')=:3
    """
    
    try:
        cursor.execute(get_sql, (home_team, away_team, game_date))
    except:
        print('경기 정보 삭제를 실패했습니다.')
        return
    
    data = cursor.fetchone()

    home_score = data[2]
    away_score = data[3]
    season = data[4]

    delete_game = """
        delete from games
        where home_team=:1 
            and away_team=:2 
            and to_char(game_date, 'YYYY-MM-DD HH24:MI')=:3
    """
    
    update_win = """
        update season_record
        set win = win-1
        where season=:1
                and team_name=:2
    """
    
    update_lose = """
        update season_record
        set lose = lose -1
        where season=:1
                and team_name=:2
    """

    update_draw = """
        update season_record
        set draw = draw-1
        where season=:1
                and team_name=:2
    """
    
    try:
        cursor.execute(delete_game, (home_team, away_team, game_date))
    except:
        print('경기 정보 삭제를 실패했습니다.')
        return
    
    try:
        if home_score > away_score: #홈팀의 승리 하나 지우기/원정팀의 패배 하나 지우기
            cursor.execute(update_win, (season, home_team))
            cursor.execute(update_lose, (season, away_team))
        elif home_score<away_score: #원정팀의 승리 하나 지우기/홈팀의 패배 하나 지우기
            cursor.execute(update_win, (season, away_team))
            cursor.execute(update_lose, (season, home_team))
        else:#홈팀과 원정팀의 무승부 하나씩 지우기
            cursor.execute(update_draw, (season, home_team))
            cursor.execute(update_draw, (season, away_team))
    except:
        print('경기 정보 삭제를 실패했습니다.')
        return


#%% 경기 정보를 수정하는 함수입니다
def update_game_info(season):
    cursor = conn.cursor()
    
    home_team = input("홈팀: ")
    away_team = input("원정팀: ")
    game_date = input("경기날짜와 시간(ex)2020-02-27 18:30): ")
    pattern = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    
    if re.fullmatch(pattern, game_date) == None:
        print('잘못된 입력값 입니다.')
        return
    home_score = input("새로 홈팀 점수: ")
    away_score = input("새로운 원정팀 점수: ")
    stadium = input("새로운 구장: ")
    
    origin_sql = """
        select home_score, away_score
        from games
        where home_team=:1 
            and away_team=:2 
            and to_char(game_date, 'YYYY-MM-DD HH24:MI')=:3
    """
    try:
        cursor.execute(origin_sql, (home_team, away_team, game_date))
    except:
        print('수정에 실패했습니다.')
        
    data = cursor.fetchone()
    ori_home_score = data[0]
    ori_away_score = data[1]
    
    sql = """
        update games
        set home_score=:1, away_score=:2, stadium=:3
        where home_team=:4
            and away_team=:5 
            and to_char(game_date, 'YYYY-MM-DD HH24:MI')=:6
    """
    
    try:
        cursor.execute(sql, (home_score, away_score, stadium, home_team, away_team, game_date))
    except:
        print('수정에 실패했습니다.')
    
    update_win_minus = """
        update season_record
        set win = win-1
        where season=:1
                and team_name=:2
    """
    update_win_plus = """
        update season_record
        set win = win+1
        where season=:1
                and team_name=:2
    """
    
    update_lose_minus = """
        update season_record
        set lose = lose -1
        where season=:1
                and team_name=:2
    """
    update_lose_plus = """
        update season_record
        set lose = lose+1
        where season=:1
                and team_name=:2
    """
    
    update_draw_minus = """
        update season_record
        set draw = draw-1
        where season=:1
                and team_name=:2
    """
    update_draw_plus = """
        update season_record
        set draw = draw+1
        where season=:1
                and team_name=:2
    """
    #원래 점수랑 바뀐 점수를 비교한다 -> 승패무가 그대로면 안바꿈 / 승패무가 바뀌면 update
    print("원래 점수 {} : {}".format(ori_home_score, ori_away_score))
    print("바뀐 점수 {} : {}".format(home_score, away_score))
    try:
        if ori_home_score > ori_away_score: #원래는 홈팀 승리 / 원정팀 패
            cursor.execute(update_win_minus, (season, home_team))
            cursor.execute(update_lose_minus, (season, away_team))
            if home_score < away_score:
                cursor.execute(update_win_plus, (season, away_team))
                cursor.execute(update_lose_plus, (season, home_team))
            elif home_score == away_score:
                cursor.execute(update_draw_plus, (season, away_team))
                cursor.execute(update_draw_plus, (season, home_team))
                
        elif ori_home_score < ori_away_score:#원래는 원정팀 승리 / 홈팀 패
            cursor.execute(update_win_minus, (season, away_team))
            cursor.execute(update_lose_minus, (season, home_team))
            if home_score > away_score:
                cursor.execute(update_win_plus, (season, home_team))
                cursor.execute(update_lose_plus, (season, away_team))
            elif home_score == away_score:
                cursor.execute(update_draw_plus, (season, home_team))
                cursor.execute(update_draw_plus, (season, away_team))
                
        else:#원래는 무승부
            cursor.execute(update_draw_minus, (season, home_team))
            cursor.execute(update_draw_minus, (season, away_team))
            if home_score > away_score:
                cursor.execute(update_win_plus, (season, home_team))
                cursor.execute(update_lose_plus, (season, away_team))
            elif home_score < away_score:
                cursor.execute(update_win_plus, (season, away_team))
                cursor.execute(update_lose_plus, (season, home_team))
    except:
        print('수정에 실패했습니다.')
        return
    
    print('성공적으로 수정했습니다.')
    
#%% 프로그램 시작하기
def start():
    while True:
        
        print("""
-------------------------------------------------------
              
              1. 로그인 하기
              2. 회원 가입
              0. 종료
              
-------------------------------------------------------
    """)
        menu = input("메뉴 선택: ")
        pattern = '[\d]+'
    
        if re.fullmatch(pattern, menu) == None:
            print('잘못된 입력값 입니다.')
            menu = -1
        else:
            menu = int(menu)
        if menu == 1:
            login()
        elif menu == 2:
            signup()
            conn.commit()
        elif menu == 0:
            conn.close()
            break
        else:
            print('다시 입력하세요.')
#%% 로그인하기
def login():
    cursor = conn.cursor()
    
    user_id = input("계정 : ")
    upassword = getpass.getpass("비밀번호: ")
    
    sql = """
        select user_id
        from puser
        where user_id =:user_id and upassword=:upassword
    """
    
    try:
        cursor.execute(sql,(user_id, upassword))
    except:
        print("로그인에 실패 했습니다.")
        return
    data = cursor.fetchall()
    
    
    if len(data) == 1:
        print()
        print("로그인에 성공 했습니다.")
        global_id = data[0][0]
        
        main(global_id)
    else:
        print()
        print("로그인에 실패 했습니다.")
        return

#%% 회원가입하기
def signup():
    cursor = conn.cursor()
    
    user_id = input("계정 : ")
    upassword = input("비밀번호: ")
    uname = input("이름: ")
    
    sql = """
        insert into puser(user_id, upassword, uname)
        values(:1,:2,:3)
    """
    try:
        cursor.execute(sql,(user_id, upassword, uname) )
    except:
        print('회원가입에 실패했습니다. 다시 시도해주세요.')
        
    
#%% 메뉴를 출력하고 입력받는 함수입니다
def print_menu():
    print('''
          
-------------------------------------------------------
          
          1. 팀별 성적 보기
          2. 경기 결과 입력하기
          3. 경기 결과 삭제하기
          4. 경기 결과 수정하기
          5. 경기 결과 보기
          6. 전체 경기 결과 내보내기(csv)
          7. 시즌 경기 결과 입력하기(csv)
          0. 종료
          
-------------------------------------------------------

          ''')
    menu = input("메뉴 선택: ")
    pattern = '[\d]+'
    
    if re.fullmatch(pattern, menu) == None:
        print('잘못된 입력값 입니다.')
        return -1
    return int(menu)
#%% 유저용 메뉴를 출력하고 입력받는 함수입니다
def print_user_menu():
    print('''
          
-------------------------------------------------------
          
          1. 팀별 성적 보기
          2. 경기 결과 보기
          0. 종료
          
-------------------------------------------------------

          ''')
    menu = input("메뉴 선택: ")
    pattern = '[\d]+'
    
    if re.fullmatch(pattern, menu) == None:
        print('잘못된 입력값 입니다.')
        return -1
    return int(menu)
#%% 무한 반복하면서 메뉴를 입력받아 선택한 메뉴와 관련된 함수를 실행시키는 메인 함수
def main(global_id):
    print(global_id,"님 안녕하세요~!!!!!!!!!!!!!!!")
    print()
    
    if global_id == 'admin':
        while True:
            
            menu = print_menu()
            if menu==1:#팀별 성적 보
                team_name = int(input("""
    팀을 선택해 주세요: 
          1.한화 이글스 2.두산 베어스 3.롯데 자이언츠 
          4.삼성 라이온즈 5.넥센 히어로즈 6.SK 와이번스 
          7.기아 타이거즈 8.KT WIZ 9.LG 트윈스 10.NC 다이노스
    :"""))
                get_team_record(team_name)
            elif menu == 2:#경기 결과 입력
                insert_game_info()
                conn.commit()
            elif menu == 3:#경기 결과 삭제
                delete_game_info()
                conn.commit()
            elif menu == 4:#경기 결과 수정
                season = input("수정할 경기 시즌을 입력하세요: ")
                update_game_info(season)
                conn.commit()
            elif menu==5:#경기 결과 보기
                date = input("경기 날짜를 입력해주세요 (ex:2020-03-14)")
                select_game(date)
            elif menu==6:#경기 결과 파일화
                export_season_info()
            elif menu==7:#파일을 DB에 입력
                season = input("입력하고 싶은 시즌을 입력해주세요(2015~2017): ")
                insert_game_season(season)
                conn.commit()
            elif menu==0:#끝!!!!!!!!!!!!
                break
            else:
                print("잘못된 입력입니다.")
            time.sleep(1)
            enter = input('진행하려면 Enter를 눌러주세요')
            while enter != '':
                enter = input('진행하려면 Enter를 눌러주세요')
    else:
        while True:
            menu = print_user_menu()
            if menu==1:
                team_name = int(input("""
팀을 선택해 주세요: 
      1.한화 이글스 2.두산 베어스 3.롯데 자이언츠 
      4.삼성 라이온즈 5.넥센 히어로즈 6.SK 와이번스 
      7.기아 타이거즈 8.KT WIZ 9.LG 트윈스 10.NC 다이노스
:"""))
                get_team_record(team_name)
            elif menu==2:
                date = input("경기 날짜를 입력해주세요 (ex:2020-03-14)")
                select_game(date)
            elif menu==0:
                break
            else:
                print("잘못된 입력입니다.")
            time.sleep(1)
            enter = input('진행하려면 Enter를 눌러주세요')
            while enter != '':
                enter = input('진행하려면 Enter를 눌러주세요')

#%% 메인입니다
import csv
import cx_Oracle as oracle
import time
import getpass
import re
oracle_dsn = oracle.makedsn(host="localhost", port=1521, sid="orcl")
if __name__ == '__main__':
    global conn
    conn = oracle.connect(dsn=oracle_dsn, user='eunbin', password='123456')
    start()
   