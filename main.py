
import os, sqlite3
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

DB_NAME = "auction.db"

KV = r"""
#:import dp kivy.metrics.dp
<TitleLabel@Label>:
    size_hint_y: None
    height: dp(48)
    font_size: "22sp"
    bold: True

<MenuButton@Button>:
    size_hint_y: None
    height: dp(54)
    font_size: "18sp"

<SimpleRow@BoxLayout>:
    size_hint_y: None
    height: dp(48)
    spacing: dp(8)

ScreenManager:
    HomeScreen:
    PeopleScreen:
    VegetableScreen:
    AuctionScreen:
    ReportScreen:
    SettingsScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(8)
        TitleLabel:
            text: "🥬 શાકભાજી ઓક્શન હિસાબ સિસ્ટમ"
        Label:
            text: "મુખ્ય મેનુ"
            size_hint_y: None
            height: dp(32)
            font_size: "18sp"
        ScrollView:
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                MenuButton:
                    text: "👨‍🌾 ખેડૂત ઉમેરો / Delete"
                    on_release: app.open_people("farmer")
                MenuButton:
                    text: "👥 ખરીદનાર ઉમેરો / Delete"
                    on_release: app.open_people("buyer")
                MenuButton:
                    text: "🥬 શાકભાજી ઉમેરો"
                    on_release: app.go("vegetable")
                MenuButton:
                    text: "📝 ઓક્શન એન્ટ્રી કરો"
                    on_release: app.go("auction")
                MenuButton:
                    text: "📊 રિપોર્ટ અને હિસાબ"
                    on_release: app.go("report")
                MenuButton:
                    text: "⚙️ Commission Settings"
                    on_release: app.go("settings")

<PeopleScreen>:
    name: "people"
    kind: "farmer"
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(8)
        TitleLabel:
            text: root.title
        TextInput:
            id: name
            hint_text: "નામ"
            multiline: False
            size_hint_y: None
            height: dp(48)
        TextInput:
            id: village
            hint_text: "ગામ (ખેડૂત માટે)"
            multiline: False
            size_hint_y: None
            height: dp(48)
        TextInput:
            id: mobile
            hint_text: "મોબાઇલ નંબર"
            multiline: False
            input_filter: "int"
            size_hint_y: None
            height: dp(48)
        Button:
            text: "💾 સેવ કરો"
            size_hint_y: None
            height: dp(52)
            on_release: root.save()
        Label:
            text: "સેવ થયેલ નામ પર ટેપ કરો, પછી Delete કરો"
            size_hint_y: None
            height: dp(30)
        Spinner:
            id: picker
            text: "નામ પસંદ કરો"
            values: root.names
            size_hint_y: None
            height: dp(48)
        Button:
            text: "🗑️ પસંદ કરેલું Delete કરો"
            size_hint_y: None
            height: dp(52)
            on_release: root.delete_selected()
        Button:
            text: "← પાછા"
            size_hint_y: None
            height: dp(48)
            on_release: app.go("home")

<VegetableScreen>:
    name: "vegetable"
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(8)
        TitleLabel:
            text: "🥬 શાકભાજી ઉમેરો"
        TextInput:
            id: veg
            hint_text: "શાકભાજીનું નામ"
            multiline: False
            size_hint_y: None
            height: dp(48)
        Button:
            text: "💾 સેવ કરો"
            size_hint_y: None
            height: dp(52)
            on_release: root.save()
        Spinner:
            id: picker
            text: "શાકભાજી પસંદ કરો"
            values: root.names
            size_hint_y: None
            height: dp(48)
        Button:
            text: "🗑️ પસંદ કરેલું Delete કરો"
            size_hint_y: None
            height: dp(52)
            on_release: root.delete_selected()
        Button:
            text: "← પાછા"
            size_hint_y: None
            height: dp(48)
            on_release: app.go("home")

<AuctionScreen>:
    name: "auction"
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        TitleLabel:
            text: "📝 ઓક્શન એન્ટ્રી"
        ScrollView:
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(7)
                TextInput:
                    id: date
                    multiline: False
                    hint_text: "તારીખ DD-MM-YYYY"
                    size_hint_y: None
                    height: dp(46)
                Spinner:
                    id: farmer
                    text: "ખેડૂત પસંદ કરો"
                    values: root.farmer_names
                    size_hint_y: None
                    height: dp(48)
                Spinner:
                    id: vegetable
                    text: "શાકભાજી પસંદ કરો"
                    values: root.vegetable_names
                    size_hint_y: None
                    height: dp(48)
                Spinner:
                    id: buyer
                    text: "ખરીદનાર પસંદ કરો"
                    values: root.buyer_names
                    size_hint_y: None
                    height: dp(48)
                TextInput:
                    id: weight
                    hint_text: "વજન (Kg)"
                    multiline: False
                    input_filter: "float"
                    size_hint_y: None
                    height: dp(48)
                    on_text: root.calculate()
                TextInput:
                    id: price
                    hint_text: "ભાવ પ્રતિ Kg"
                    multiline: False
                    input_filter: "float"
                    size_hint_y: None
                    height: dp(48)
                    on_text: root.calculate()
                Label:
                    text: root.amount_text
                    markup: True
                    size_hint_y: None
                    height: dp(80)
                    font_size: "18sp"
                SimpleRow:
                    Button:
                        text: "💾 સેવ / Update"
                        on_release: root.save()
                    Button:
                        text: "🧹 સાફ"
                        on_release: root.clear_form()
                Label:
                    text: "છેલ્લી 100 એન્ટ્રીઓ — Edit/Delete માટે પસંદ કરો"
                    size_hint_y: None
                    height: dp(35)
                Spinner:
                    id: entry_picker
                    text: "ઓક્શન એન્ટ્રી પસંદ કરો"
                    values: root.history_values
                    size_hint_y: None
                    height: dp(54)
                SimpleRow:
                    Button:
                        text: "✏️ Edit"
                        on_release: root.edit_selected()
                    Button:
                        text: "🗑️ Delete"
                        on_release: root.delete_selected()
                Button:
                    text: "← પાછા"
                    size_hint_y: None
                    height: dp(48)
                    on_release: app.go("home")

<ReportScreen>:
    name: "report"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        TitleLabel:
            text: "📊 રિપોર્ટ અને હિસાબ"
        TextInput:
            id: date
            multiline: False
            hint_text: "તારીખ DD-MM-YYYY"
            size_hint_y: None
            height: dp(48)
        Button:
            text: "📊 તારીખનો સંપૂર્ણ ઓક્શન રિપોર્ટ"
            size_hint_y: None
            height: dp(52)
            on_release: root.daily_report()
        Button:
            text: "💰 ચુકવણું અને ઉઘરાણું"
            size_hint_y: None
            height: dp(52)
            on_release: root.payment_report()
        Button:
            text: "📊 તમામ ઓક્શનનો કુલ હિસાબ"
            size_hint_y: None
            height: dp(52)
            on_release: root.full_report()
        ScrollView:
            Label:
                id: output
                text: root.report_text
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1] + dp(20)
                padding: dp(8), dp(8)
                valign: "top"
        Button:
            text: "← પાછા"
            size_hint_y: None
            height: dp(48)
            on_release: app.go("home")

<SettingsScreen>:
    name: "settings"
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(10)
        TitleLabel:
            text: "⚙️ Commission Settings"
        Label:
            text: "કમિશન ટકા (%)"
            size_hint_y: None
            height: dp(35)
        TextInput:
            id: commission
            multiline: False
            input_filter: "float"
            size_hint_y: None
            height: dp(50)
        Button:
            text: "💾 કમિશન સેવ કરો"
            size_hint_y: None
            height: dp(52)
            on_release: root.save()
        Button:
            text: "← પાછા"
            size_hint_y: None
            height: dp(48)
            on_release: app.go("home")
"""

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self.create()
    def close(self):
        self.conn.close()
    def create(self):
        c=self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS farmers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,village TEXT,mobile TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS buyers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,mobile TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS vegetables(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL)")
        c.execute("""CREATE TABLE IF NOT EXISTS auctions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,auction_date TEXT NOT NULL,
            farmer_id INTEGER,vegetable_id INTEGER,buyer_id INTEGER,
            weight REAL NOT NULL,price REAL NOT NULL,total REAL NOT NULL,
            commission REAL DEFAULT 10,farmer_amount REAL NOT NULL)""")
        c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('commission_percent','10')")
        self.conn.commit()
    def rows(self, sql, params=()):
        return self.conn.execute(sql,params).fetchall()
    def one(self, sql, params=()):
        return self.conn.execute(sql,params).fetchone()
    def run(self, sql, params=()):
        self.conn.execute(sql,params); self.conn.commit()

class BaseScreen(Screen):
    def msg(self, title, text):
        box=BoxLayout(orientation="vertical",padding=10,spacing=10)
        box.add_widget(Label(text=text))
        b=Button(text="OK",size_hint_y=None,height=48)
        box.add_widget(b)
        p=Popup(title=title,content=box,size_hint=(.82,.42),auto_dismiss=False)
        b.bind(on_release=p.dismiss); p.open()

class HomeScreen(BaseScreen): pass

class PeopleScreen(BaseScreen):
    kind=StringProperty("farmer")
    title=StringProperty("👨‍🌾 ખેડૂત")
    names=ListProperty([])
    def on_pre_enter(self,*a): self.refresh()
    def refresh(self):
        app=App.get_running_app(); table="farmers" if self.kind=="farmer" else "buyers"
        rows=app.db.rows(f"SELECT * FROM {table} ORDER BY name")
        self.names=[(r["name"]+(f" ({r['village']})" if self.kind=="farmer" and r["village"] else "")) for r in rows]
        self.ids.picker.values=self.names
        self.ids.picker.text="નામ પસંદ કરો"
        self.ids.village.disabled=self.kind!="farmer"
    def save(self):
        name=self.ids.name.text.strip(); mobile=self.ids.mobile.text.strip(); village=self.ids.village.text.strip()
        if not name: return self.msg("Error","નામ લખો.")
        app=App.get_running_app()
        try:
            if self.kind=="farmer": app.db.run("INSERT INTO farmers(name,village,mobile) VALUES(?,?,?)",(name,village,mobile))
            else: app.db.run("INSERT INTO buyers(name,mobile) VALUES(?,?)",(name,mobile))
            self.ids.name.text=self.ids.mobile.text=self.ids.village.text=""
            self.refresh(); self.msg("Success","સફળતાપૂર્વક સેવ થયું.")
        except sqlite3.IntegrityError: self.msg("Error","આ નામ પહેલેથી હાજર છે.")
    def delete_selected(self):
        selected=self.ids.picker.text
        if selected=="નામ પસંદ કરો": return self.msg("માહિતી","નામ પસંદ કરો.")
        name=selected.split(" (")[0]; app=App.get_running_app()
        table="farmers" if self.kind=="farmer" else "buyers"; col="farmer_id" if self.kind=="farmer" else "buyer_id"
        row=app.db.one(f"SELECT id FROM {table} WHERE name=?",(name,))
        if app.db.one(f"SELECT COUNT(*) c FROM auctions WHERE {col}=?",(row["id"],))["c"]:
            return self.msg("માહિતી","આ નામ સાથે ઓક્શન એન્ટ્રીઓ છે, તેથી Delete કરી શકાતું નથી.")
        app.db.run(f"DELETE FROM {table} WHERE id=?",(row["id"],)); self.refresh(); self.msg("Success","નામ Delete થયું.")

class VegetableScreen(BaseScreen):
    names=ListProperty([])
    def on_pre_enter(self,*a): self.refresh()
    def refresh(self):
        app=App.get_running_app(); self.names=[r["name"] for r in app.db.rows("SELECT name FROM vegetables ORDER BY name")]
        self.ids.picker.values=self.names
    def save(self):
        name=self.ids.veg.text.strip()
        if not name:return self.msg("Error","શાકભાજીનું નામ લખો.")
        try: App.get_running_app().db.run("INSERT INTO vegetables(name) VALUES(?)",(name,)); self.ids.veg.text=""; self.refresh(); self.msg("Success","શાકભાજી સેવ થયું.")
        except sqlite3.IntegrityError:self.msg("Error","આ શાકભાજી પહેલેથી હાજર છે.")
    def delete_selected(self):
        n=self.ids.picker.text
        if n=="શાકભાજી પસંદ કરો":return self.msg("માહિતી","શાકભાજી પસંદ કરો.")
        app=App.get_running_app(); row=app.db.one("SELECT id FROM vegetables WHERE name=?",(n,))
        if app.db.one("SELECT COUNT(*) c FROM auctions WHERE vegetable_id=?",(row["id"],))["c"]: return self.msg("માહિતી","આ શાકભાજી સાથે ઓક્શન એન્ટ્રીઓ છે.")
        app.db.run("DELETE FROM vegetables WHERE id=?",(row["id"],)); self.refresh()

class AuctionScreen(BaseScreen):
    farmer_names=ListProperty([]); buyer_names=ListProperty([]); vegetable_names=ListProperty([]); history_values=ListProperty([])
    amount_text=StringProperty("કુલ : ₹ 0.00\\nકમિશન : ₹ 0.00\\nખેડૂતને : ₹ 0.00")
    editing_id=NumericProperty(0)
    history_map={}
    def on_pre_enter(self,*a):
        self.ids.date.text=datetime.now().strftime("%d-%m-%Y"); self.refresh_lists(); self.load_history()
    def refresh_lists(self):
        app=App.get_running_app()
        self.farmer_names=[r["name"]+(f" ({r['village']})" if r["village"] else "") for r in app.db.rows("SELECT * FROM farmers ORDER BY name")]
        self.buyer_names=[r["name"] for r in app.db.rows("SELECT name FROM buyers ORDER BY name")]
        self.vegetable_names=[r["name"] for r in app.db.rows("SELECT name FROM vegetables ORDER BY name")]
    def calculate(self):
        try:
            total=float(self.ids.weight.text or 0)*float(self.ids.price.text or 0)
        except: total=0
        comm=total*App.get_running_app().commission()/100
        self.amount_text=f"કુલ : ₹ {total:.2f}\\nકમિશન : ₹ {comm:.2f}\\nખેડૂતને : ₹ {total-comm:.2f}"
    def ids_for_names(self):
        app=App.get_running_app()
        f=self.ids.farmer.text.split(" (")[0]; v=self.ids.vegetable.text; b=self.ids.buyer.text
        fr=app.db.one("SELECT id FROM farmers WHERE name=?",(f,)); vr=app.db.one("SELECT id FROM vegetables WHERE name=?",(v,)); br=app.db.one("SELECT id FROM buyers WHERE name=?",(b,))
        return (fr["id"] if fr else None, vr["id"] if vr else None, br["id"] if br else None)
    def save(self):
        try: w=float(self.ids.weight.text); p=float(self.ids.price.text)
        except:return self.msg("Error","વજન અને ભાવ સાચા લખો.")
        ids=self.ids_for_names()
        if not all(ids):return self.msg("Error","ખેડૂત, શાકભાજી અને ખરીદનાર પસંદ કરો.")
        total=w*p; cp=App.get_running_app().commission(); fam=total-total*cp/100; app=App.get_running_app()
        if self.editing_id:
            app.db.run("""UPDATE auctions SET auction_date=?,farmer_id=?,vegetable_id=?,buyer_id=?,weight=?,price=?,total=?,commission=?,farmer_amount=? WHERE id=?""",
                       (self.ids.date.text.strip(),*ids,w,p,total,cp,fam,self.editing_id))
        else:
            app.db.run("""INSERT INTO auctions(auction_date,farmer_id,vegetable_id,buyer_id,weight,price,total,commission,farmer_amount) VALUES(?,?,?,?,?,?,?,?,?)""",
                       (self.ids.date.text.strip(),*ids,w,p,total,cp,fam))
        self.clear_form(); self.load_history(); self.msg("Success","એન્ટ્રી સેવ/સુધારાઈ ગઈ.")
    def clear_form(self):
        self.editing_id=0; self.ids.weight.text=""; self.ids.price.text=""; self.calculate()
    def load_history(self):
        app=App.get_running_app()
        rows=app.db.rows("""SELECT a.id,a.auction_date,f.name farmer,v.name veg,b.name buyer,a.weight,a.price,a.total FROM auctions a
        JOIN farmers f ON f.id=a.farmer_id JOIN vegetables v ON v.id=a.vegetable_id JOIN buyers b ON b.id=a.buyer_id ORDER BY a.id DESC LIMIT 100""")
        self.history_map={}; vals=[]
        for r in rows:
            s=f"ID:{r['id']} | {r['auction_date']} | {r['farmer']} | {r['veg']} | {r['weight']:g} Kg × ₹{r['price']:.2f} = ₹{r['total']:.2f} | {r['buyer']}"
            vals.append(s); self.history_map[s]=r["id"]
        self.history_values=vals; self.ids.entry_picker.values=vals; self.ids.entry_picker.text="ઓક્શન એન્ટ્રી પસંદ કરો"
    def selected_id(self): return self.history_map.get(self.ids.entry_picker.text)
    def edit_selected(self):
        aid=self.selected_id()
        if not aid:return self.msg("માહિતી","પહેલા એન્ટ્રી પસંદ કરો.")
        r=App.get_running_app().db.one("SELECT * FROM auctions WHERE id=?",(aid,)); app=App.get_running_app()
        self.editing_id=aid; self.ids.date.text=r["auction_date"]
        fr=app.db.one("SELECT name,village FROM farmers WHERE id=?",(r["farmer_id"],)); self.ids.farmer.text=fr["name"]+(f" ({fr['village']})" if fr["village"] else "")
        self.ids.vegetable.text=app.db.one("SELECT name FROM vegetables WHERE id=?",(r["vegetable_id"],))["name"]
        self.ids.buyer.text=app.db.one("SELECT name FROM buyers WHERE id=?",(r["buyer_id"],))["name"]
        self.ids.weight.text=str(r["weight"]); self.ids.price.text=str(r["price"]); self.calculate()
    def delete_selected(self):
        aid=self.selected_id()
        if not aid:return self.msg("માહિતી","પહેલા એન્ટ્રી પસંદ કરો.")
        App.get_running_app().db.run("DELETE FROM auctions WHERE id=?",(aid,)); self.load_history(); self.msg("Success","ઓક્શન એન્ટ્રી Delete થઈ.")

class ReportScreen(BaseScreen):
    report_text=StringProperty("")
    def on_pre_enter(self,*a): self.ids.date.text=datetime.now().strftime("%d-%m-%Y")
    def daily_report(self):
        d=self.ids.date.text.strip(); app=App.get_running_app()
        s=app.db.one("""SELECT COUNT(*) entries,COALESCE(SUM(total),0) gross,COALESCE(SUM(total*commission/100),0) comm,COALESCE(SUM(farmer_amount),0) payable,COALESCE(SUM(weight),0) weight FROM auctions WHERE auction_date=?""",(d,))
        veg=app.db.rows("""SELECT v.name,SUM(a.weight) weight,SUM(a.total) total FROM auctions a JOIN vegetables v ON v.id=a.vegetable_id WHERE a.auction_date=? GROUP BY v.id ORDER BY total DESC""",(d,))
        buyers=app.db.rows("""SELECT b.name,SUM(a.total) total FROM auctions a JOIN buyers b ON b.id=a.buyer_id WHERE a.auction_date=? GROUP BY b.id ORDER BY total DESC""",(d,))
        text=f"દૈનિક સંપૂર્ણ ઓક્શન રિપોર્ટ\\nતારીખ: {d}\\n\\nકુલ એન્ટ્રીઓ: {s['entries']}\\nકુલ વજન: {s['weight']:g} Kg\\nકુલ વેચાણ: ₹{s['gross']:.2f}\\nકુલ કમિશન: ₹{s['comm']:.2f}\\nખેડૂતોને ચુકવવાનું: ₹{s['payable']:.2f}\\nખરીદદારો પાસેથી લેવાનું: ₹{s['gross']:.2f}\\n\\nશાકભાજી પ્રમાણે\\n"
        text+="\\n".join(f"{r['name']} — {r['weight']:g} Kg — ₹{r['total']:.2f}" for r in veg) or "કોઈ એન્ટ્રી નથી."
        text+="\\n\\nખરીદદાર પ્રમાણે\\n"+("\\n".join(f"{r['name']} — ₹{r['total']:.2f}" for r in buyers) or "કોઈ એન્ટ્રી નથી.")
        self.report_text=text
    def payment_report(self):
        d=self.ids.date.text.strip(); app=App.get_running_app()
        fr=app.db.rows("""SELECT f.name,COALESCE(f.village,'') village,SUM(a.total) gross,SUM(a.total*a.commission/100) comm,SUM(a.farmer_amount) payable FROM auctions a JOIN farmers f ON f.id=a.farmer_id WHERE a.auction_date=? GROUP BY f.id ORDER BY f.name""",(d,))
        br=app.db.rows("""SELECT b.name,SUM(a.total) receivable FROM auctions a JOIN buyers b ON b.id=a.buyer_id WHERE a.auction_date=? GROUP BY b.id ORDER BY b.name""",(d,))
        pg=sum(r["gross"] for r in fr); pc=sum(r["comm"] for r in fr); pay=sum(r["payable"] for r in fr); rec=sum(r["receivable"] for r in br)
        text=f"તારીખ પ્રમાણે ચુકવણું અને ઉઘરાણું\\nતારીખ: {d}\\n\\nખેડૂતોને ચુકવવાના રૂપિયા\\n"
        text+="\\n".join(f"{r['name']} ({r['village']}) — કુલ ₹{r['gross']:.2f} | કમિશન ₹{r['comm']:.2f} | ચુકવવા ₹{r['payable']:.2f}" for r in fr) or "કોઈ એન્ટ્રી નથી."
        text+=f"\\n\\nકુલ વેચાણ: ₹{pg:.2f}\\nકુલ કમિશન: ₹{pc:.2f}\\nખેડૂતોને કુલ ચુકવણું: ₹{pay:.2f}\\n\\nખરીદદારો પાસેથી ઉઘરાવવાના રૂપિયા\\n"
        text+="\\n".join(f"{r['name']} — ₹{r['receivable']:.2f}" for r in br) or "કોઈ એન્ટ્રી નથી."
        text+=f"\\n\\nકુલ ઉઘરાણું: ₹{rec:.2f}"; self.report_text=text
    def full_report(self):
        s=App.get_running_app().db.one("SELECT COUNT(*) entries,COALESCE(SUM(total),0) sales,COALESCE(SUM(farmer_amount),0) payable FROM auctions")
        self.report_text=f"શાકભાજી ઓક્શન સંપૂર્ણ હિસાબ\\n\\nકુલ ઓક્શન એન્ટ્રી: {s['entries']}\\nકુલ વેચાણ: ₹{s['sales']:.2f}\\nકુલ કમિશન: ₹{s['sales']-s['payable']:.2f}\\nખેડૂતોને ચૂકવવાની રકમ: ₹{s['payable']:.2f}"

class SettingsScreen(BaseScreen):
    def on_pre_enter(self,*a): self.ids.commission.text=str(App.get_running_app().commission())
    def save(self):
        try:v=float(self.ids.commission.text)
        except:return self.msg("Error","માન્ય કમિશન ટકા લખો.")
        if not 0<=v<=100:return self.msg("Error","કમિશન 0 થી 100 વચ્ચે હોવું જોઈએ.")
        App.get_running_app().db.run("INSERT OR REPLACE INTO settings(key,value) VALUES('commission_percent',?)",(str(v),)); self.msg("Success",f"કમિશન {v:g}% સેવ થયું.")

class VegetableAuctionApp(App):
    def build(self):
        self.db=DB(); return Builder.load_string(KV)
    def commission(self):
        return float(self.db.one("SELECT value FROM settings WHERE key='commission_percent'")["value"])
    def go(self,name): self.root.current=name
    def open_people(self,kind):
        s=self.root.get_screen("people"); s.kind=kind; s.title="👨‍🌾 ખેડૂત ઉમેરો / વ્યવસ્થા" if kind=="farmer" else "👥 ખરીદનાર ઉમેરો / વ્યવસ્થા"; self.go("people")
    def on_stop(self): self.db.close()

if __name__=="__main__":
    VegetableAuctionApp().run()
