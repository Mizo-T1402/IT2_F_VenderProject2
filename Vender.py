
import csv
import time
import os
from collections import defaultdict

# ---------- データクラス ----------

class Item:
    def __init__(self, code, name, price, stock):
        self.code = code
        self.name = name
        self.price = price
        self.stock = stock


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
        if self.inserted_count[value] >= limit:
            print("\033[31m 投入枚数が上限(20枚)を超えています。\033[0m")
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


# ---------- 商品管理 ----------

class ItemManager:
    ITEM_KEYS = {"A", "B", "C", "D", "E"}

    def __init__(self, money_manager):
        self.items = []
        self.money_manager = money_manager

    def load_items(self, filepath):
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.items.append(
                    Item(row["code"], row["name"], int(row["price"]), int(row["stock"]))
                )

    def save_items(self, filepath):
        #itemの内容をcsvに書き込み
        with open(filepath, mode = "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(['code','name','price','stock'])
            for item in self.items:
                writer.writerow([item.code,item.name,item.price,item.stock])

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
            return False

        if self.money_manager.inserted_total < item.price:
            return False

        change = self.money_manager.inserted_total - item.price
        if not self.money_manager.can_return_change(change):
            print("\033[31m 硬貨の釣銭切れのため購入できません。\033[0m")
            return False

        # 払出
        item.stock -= 1
        self.money_manager.return_change(change)

        # csvに保存
        self.save_items("items.csv")
        self.money_manager.save_money("money.csv")

        print(f"\033[34m \n{item.name} の購入ありがとうございました。\033[0m")
        if change > 0:
            print(f"\033[34mお釣り {change}円 をお受け取りください。\033[0m")

        time.sleep(10)
        self.money_manager.reset()
        return True


# ---------- メイン制御 ----------

class VendMachineController:
    def __init__(self):
        self.money = MoneyManager()
        self.items = ItemManager(self.money)

    def setup(self):
        self.items.load_items("items.csv")
        self.money.load_money("money.csv")

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
                time.sleep(10)
                break

            if key in MoneyManager.MONEY_KEYS:
                self.money.insert_money(key)
            elif key in ItemManager.ITEM_KEYS:
                self.items.select_item(key)


# ---------- 実行 ----------

if __name__ == "__main__":
    VendMachineController().run()