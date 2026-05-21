
import csv
import time
import os
from collections import defaultdict

# ---------- データクラス ----------

class Item:
    def __init__(self, code, name, price, stock, sales, total): #salesとtotalの追加、各商品の各売上個数と売上金額が見れる（仕様書にない仕様）
        self.code = code
        self.name = name
        self.price = price
        self.stock = stock
        self.sales = sales
        self.total = total


# ---------- 金銭管理 ----------

class MoneyManager:
    MONEY_KEYS = {
        "1": 10,
        "2": 50,
        "3": 100,
        "4": 500,
        "5": 1000
    }

    def __init__(self):
        self.money_stock = {}
        self.inserted_total = 0
        self.inserted_count = defaultdict(int)

    def load_money(self, filepath):
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.money_stock[int(row["denomination"])] = int(row["count"])

    def save_money(self, filepath):
        with open(filepath, mode = "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(['denomination','count'])
            for coin in [10, 50, 100, 500, 1000]:
                writer.writerow([coin,self.money_stock[coin]])

    def insert_money(self, key):
        value = self.MONEY_KEYS[key]

        # 上限チェック
        limit = 2 if value == 1000 else 20
        if self.inserted_total + value >= 2000: #投入金額上限設定
            print("\033[31m 投入金額を超えています。\033[0m]]")
            time.sleep(1) #表示時間延長
            return
        
        elif self.inserted_count[value] >= limit:
            print("\033[31m 投入枚数が上限(20枚)を超えています。\033[0m")
            time.sleep(1) #表示時間延長
            return

        self.inserted_total += value
        self.inserted_count[value] += 1
        self.money_stock[value] += 1

    def can_return_change(self, change):
        remaining = change
        for coin in [1000, 500, 100, 50, 10]:
            use = min(self.money_stock.get(coin, 0), remaining // coin)
            remaining -= use * coin
        return remaining == 0

    def return_change(self, change):
        remaining = change
        for coin in [1000, 500, 100, 50, 10]:
            use = min(self.money_stock.get(coin, 0), remaining // coin)
            self.money_stock[coin] -= use
            remaining -= use * coin
        
    def reset(self):
        self.inserted_total = 0
        self.inserted_count.clear()


# -----売上管理----追加部分＿溝

class SalesManager: #合計売上の管理を行うクラス
    def __init__(self):
        self.amount_read = [] #読み取り用
        self.amount = 0 #計算用、ここに都度の更新をため込んでいる

    def load_sales(self, filepath): #読み込み用インスタンス、行を指定して合計売上の数値だけを取得している
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            first_row = next(reader)
            self.amount_read.append(int(first_row["amount"]))
        self.amount = self.amount_read[0]

    def sales_cal(self, sale): #計算用、クラス内のamountを常に更新している
        self.amount += sale

    def save_sales(self, filepath): #書き込み用
        #salesの内容をcsvに書き込み
        with open(filepath, mode = "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(['amount'])
            writer.writerow([self.amount])



# ---------- 商品管理 ----------

class ItemManager:
    ITEM_KEYS = {"A", "B", "C", "D", "E", "F"} #商品追加

    def __init__(self, money_manager, sales_manager):
        self.items = []
        self.money_manager = money_manager
        self.sales_manager = sales_manager #追加部分＿溝、いらないのかも？
        self.sales = SalesManager() #追加部分＿溝、クラス呼び出し用

    def load_items(self, filepath):
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.items.append(
                    Item(row["code"], row["name"], int(row["price"]), int(row["stock"]),int(row["sales"]), int(row["total"])) #salesとtotalの追加
                )

    def save_items(self, filepath):
        #itemの内容をcsvに書き込み
        with open(filepath, mode = "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(['code','name','price','stock','sales','total'])
            for item in self.items:
                writer.writerow([item.code,item.name,item.price,item.stock,item.sales,item.total]) #salesとtotalの追加

    def display_items(self):
        for item in self.items:
            if item.stock == 0:
                print(f"{item.code} {item.name}\033[31m  売切\033[0m")
            elif item.price <= self.money_manager.inserted_total:
               print(f"{item.code} {item.name}\033[34m {item.price}円 \033[0m")
            else:
                print(f"{item.code} {item.name} {item.price}円")

    def select_item(self, code):
        item = next((i for i in self.items if i.code == code), None)

        if item.stock == 0:
            print("\033[31m 売切れ商品です。他の商品を選択してください。\033[0m")
            time.sleep(1) #表示時間延長
            return False

        if self.money_manager.inserted_total < item.price:
            shotage = item.price - self.money_manager.inserted_total
            print(f"\033[31m 投入金が{shotage}円不足しています。お金を追加してください。\033[0m") #メッセージ表示追加
            time.sleep(1)
            return False

        change = self.money_manager.inserted_total - item.price
        if not self.money_manager.can_return_change(change):
            print("\033[31m 硬貨の釣銭切れのため購入できません。\033[0m")
            time.sleep(1) #表示時間延長
            return False

        # 払出
        item.stock -= 1
        item.sales += 1 #salesの計算の追加
        item.total += item.price #totalの計算を追加
        self.sales_manager.sales_cal(item.price) #追加部分＿溝、合計売上金額の計算
        self.money_manager.return_change(change)

        # csvに保存
        self.save_items("items.csv")
        self.money_manager.save_money("money.csv")
        self.sales_manager.save_sales("sales.csv") #追加部分＿溝、csvへの書き込み

        print(f"\033[34m \n{item.name} の購入ありがとうございました。\033[0m")
        if change > 0:
            print(f"\033[34mお釣り {change}円 をお受け取りください。\033[0m")
        
        print("準備中です。しばらくお待ちください。") #メッセージ表示追加
        time.sleep(10)
        self.money_manager.reset()
        return True


# ---------- メイン制御 ----------

class VendMachineController:
    def __init__(self):
        self.money = MoneyManager()
        self.sales = SalesManager() #追加部分＿溝、呼び出しにのみ使用
        self.items = ItemManager(self.money,self.sales)

    def setup(self):
        self.items.load_items("items.csv")
        self.money.load_money("money.csv")
        self.sales.load_sales("sales.csv") #追加部分＿溝、読み込み

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def run(self):
        self.setup()

        while True:
            self.clear()
            print("*** 自動販売機 シミュレーション ソフトウェア ***")
            self.items.display_items()
            print(f"\n投入金額: {self.money.inserted_total}円")
            print("お金を入れてください。 1=10円 2=50円 3=100円 4=500円 5=1000円")

            key = input(">> ").strip().upper()

            if key == "9":
                if self.money.inserted_total > 0:
                    print(f"返金 {self.money.inserted_total}円")

                print( "プログラムを終了します。しばらくお待ちください。") #メッセージ表示追加
                time.sleep(10)
                    
                break

            if key in MoneyManager.MONEY_KEYS:
                self.money.insert_money(key)
            elif key in ItemManager.ITEM_KEYS:
                self.items.select_item(key)
            else:
                print("\033[31m 入力エラー。再度入力してください。\033[0m") #メッセージ表示追加
                time.sleep(1)


# ---------- 実行 ----------

if __name__ == "__main__":
    VendMachineController().run()