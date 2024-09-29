import tkinter as tk
from tkinter import ttk
import json, datetime, os, fitz
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageTk


# Fişi pdf olarak oluşturmak için fonksiyon
def CreateReceipt(products, user_id):
    now = datetime.datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S") # Anlık zamanı çekeren pdf e eşsiz bir isim oluşturuyoruz
    folder_path = f'./fişler/{user_id}/'
    os.makedirs(folder_path, exist_ok=True) # Dizin yok ise oluştur
    filename = f'{folder_path}fis_{date_time}.pdf'

    # PDF dosyasını oluştur
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # FreeSerif yazı tipini kaydet ve kullan
    pdfmetrics.registerFont(TTFont('FreeSerif', 'FreeSerif.ttf'))
    c.setFont('FreeSerif', 16)
    
    # Başlık ekle
    c.drawString(250, height - 40, 'Alışveriş Fişi')
    
    # Ürün bilgilerini ekle
    c.setFont('FreeSerif', 12)
    y = height - 80
    c.drawString(50, y, 'Ürün Adı')
    c.drawString(250, y, 'Adet')
    c.drawString(350, y, 'Adet Fiyatı')
    c.drawString(450, y, 'Toplam Fiyat')
    
    y -= 20
    toplam_tutar = 0

    # Her ürünü pdf e ekle
    for product in products:
        urun_adi = product['product']
        adet = product['quantity']
        adet_fiyati = product['price']
        toplam_fiyat = adet * adet_fiyati
        toplam_tutar += toplam_fiyat
        
        c.drawString(50, y, urun_adi)
        c.drawString(250, y, str(adet))
        c.drawString(350, y, f"{adet_fiyati:.2f} TL")
        c.drawString(450, y, f"{toplam_fiyat:.2f} TL")
        
        y -= 20
        
    # Toplam tutarı ekle
    c.setFont('FreeSerif', 12)
    c.drawString(350, y - 20, 'Toplam Tutar:')
    c.drawString(450, y - 20, f"{toplam_tutar:.2f} TL")
    
    # PDF dosyasını kaydet
    c.save()

    return f"{folder_path}fis_{date_time}.pdf"

# Kullanıcıları okuyup döndür
def ReadUsers():
    with open('./settings/users.json', 'r', encoding="utf8") as file:
        data = json.load(file)
    return data

# Statüse göre ürünleri okuyup döndür
def ReadProducts(status=1):

    if status == 1:
        with open('./products/foods.json', 'r', encoding="utf8") as file:
            data = json.load(file)

    elif status == 2:
        with open('./products/desserts.json', 'r', encoding="utf8") as file:
            data = json.load(file)

    elif status == 3:
        with open('./products/drinks.json', 'r', encoding="utf8") as file:
            data = json.load(file)

    return data


# Verilen bilgilere göre kullanıcıyı ekle
def AddUser(email, password, full_name, is_admin=False):
    users_file = "./settings/users.json"
    with open(users_file, 'r') as file:
        users = json.load(file) # Tüm kullanıcıları çek

    for user in users:
        if user["email"] == email: # E-potanın varlığını kontrol et
            return [False, "E-Posta zaten mevcut"]
        
    if users:
        max_id = max(users, key=lambda x: x["id"])["id"] # en yüksek id değerini bul
        new_id = max_id + 1
    else:
        new_id = 1  # İlk kullanıcı için ID 1

    # Yeni kullanıcıyı oluştur
    new_user = {
        "id": new_id,
        "email": email,
        "password": password,
        "full_name": full_name,
        "is_admin": is_admin
    }

    users.append(new_user)

    with open(users_file, 'w') as file:
        json.dump(users, file, indent=4) # Kullanıcılar listesinin yeni halini dosyaya yazdır

    return [True, "Kayıt Olundu"]

# Tkinter da inputların içerisine metin eklemek için oluşturulmuş sınıf
class PlaceholderEntry(ttk.Entry):
    def __init__(self, container, placeholder, width=None, height=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs, width=width, height=height)
        self.placeholder = placeholder
        self.default_fg_color = self['foreground']

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._set_placeholder)

        self._set_placeholder()

    def _clear_placeholder(self, event=None):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(foreground=self.default_fg_color)

    def _set_placeholder(self, event=None):
        if not self.get() and not self.focus_get():
            self.insert(0, self.placeholder)
            self.config(foreground='gray')

# Ana proje sınıfımız
class RestaurantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yemek Sipariş Uygulaması")
        self.geometry("700x450")

        # Tüm sayfaları tutacak ana container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # İlerleyen kısımlarda kullanılacak gerekli tanımlamalar
        self.frames = {}
        self.login_user = None
        self.cart = []
        self.receipt = ""
        color = "#e38828"

        # Tüm sınıflardan bir sayfa oluşturuyor
        for F in (HomePage, LoginPage, RegisterPage, MenuPage, FoodsPage, DessertsPage, DrinksPage, ReceiptPage, AdminPage, FoodAddPage, DessertAddPage, DrinkAddPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self, bg_color=color)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    # İstediğimiz sayfaya gitmemeizi sağlayan fonksiyon
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if page_name == "MenuPage" and hasattr(frame, "load_page"): # Eğer menüye gidelmek istenirse ilk önce sayfayı güncelle
            frame.load_page()
        elif page_name == "ReceiptPage" and hasattr(frame, "load_page"):# Eğer fiş sayfasına gidelmek istenirse ilk önce sayfayı güncelle
            frame.load_page()
        elif page_name == "FoodAddPage" and hasattr(frame, "load_page"):# Eğer yemek ekleme sayfasına gidelmek istenirse ilk önce sayfayı güncelle
            frame.load_page()
        elif page_name == "DessertAddPage" and hasattr(frame, "load_page"):# Eğer tatlı ekleme sayfasına gidelmek istenirse ilk önce sayfayı güncelle
            frame.load_page()
        elif page_name == "DrinkAddPage" and hasattr(frame, "load_page"):# Eğer içecek ekleme sayfasına  gidelmek istenirse ilk önce sayfayı güncelle
            frame.load_page()
        frame.tkraise()

# Bizi ilk karşılıcak anasayfa sınıfı
class HomePage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)  # Arka plan rengini burada ayarlayın
        self.controller = controller

        # Hoşgeldin yazısı oluşturup sayfada konumladır
        welcome_label = tk.Label(self, text="Hoş Geldiniz!\n\nSipariş oluşturmak için\nLütfen giriş yapın veya kayıt olun.", bg=bg_color, font=("Helvetica", 16), fg="white")
        welcome_label.place(x="140px", y="110px")

        # Giriş Yap butonu oluşturup sayfada konumladır
        login_page_btn = tk.Button(self, text="Giriş Yap", command=lambda: controller.show_frame("LoginPage"), width=16, bg="white", fg="black")
        login_page_btn.place(x="170px", y="210px")

        # Kayıt Ol butonu oluşturup sayfada konumladır
        register_page_btn = tk.Button(self, text="Kayıt Ol", command=lambda: controller.show_frame("RegisterPage"), width=16, bg="white", fg="black")
        register_page_btn.place(x="265px", y="210px")

        # Hover efektleri için butonlara bind ekle
        self.add_hover_effect(login_page_btn)
        self.add_hover_effect(register_page_btn)

    # Butonlara Hover Efekti veren fonksiyon
    def add_hover_effect(self, button):
        button.bind("<Enter>", lambda e: button.config(bg="#e38828", fg="white"))
        button.bind("<Leave>", lambda e: button.config(bg="white", fg="black"))

# Giriş yapma sayfasının sınıfı
class LoginPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color) 
        self.controller = controller

        label = tk.Label(self, text="Giriş Yap", font=("Helvetica", 16), bg=bg_color, fg="white")
        label.pack(pady=140)

        # Email inputu oluşturup sayfada konumlandır
        email_entry = PlaceholderEntry(self, "E-posta", width=30)
        email_entry.place(x="195px", y="200")

        #Parola inputu oluşturup sayfada konumlandır
        password_entry = PlaceholderEntry(self, "Parola", width=30)
        password_entry.place(x="195px", y="240")

        login_button = tk.Button(self, text="Giriş Yap", command=lambda: self.LoginCheck(email_entry.get(), password_entry.get()), width=16, bg="white", fg="black")
        login_button.place(x="220px", y="280")

        # Anasayfaya geri dönmek için geri butonu oluşturup sayfada konumlandır
        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("HomePage"), width=16, bg="white", fg="black")
        back_button.place(x="220px", y="310")

        # Hover efektleri için butonlara bind ekle
        self.add_hover_effect(login_button)
        self.add_hover_effect(back_button)

    def add_hover_effect(self, button):
        button.bind("<Enter>", lambda e: button.config(bg="#e38828", fg="white"))
        button.bind("<Leave>", lambda e: button.config(bg="white", fg="black"))

    #Giriş yap butonuna basınca çalışacak fonksiyon
    def LoginCheck(self, email, password):
        email = str(email).strip().replace("E-posta", "")
        password = str(password).strip().replace("Parola", "")
        if len(email) <= 0 and len(password) <= 0:
            print("Lütfen tüm boşlukları doldurunuz")
        else:
            users = ReadUsers() # Tüm kullanıcıların bilgisini çek

            for user in users:
                if email == user["email"]: # Girilen mail varmı kontrol et
                    if password == user["password"]:# Girilen mail var ise parola uyuşuyormu kontrol et
                        print("Giriş Başarılı")
                        self.controller.login_user = user
                        break
                    else:
                        self.controller.login_user = None
                        print("Şifre Hatalı")

            if self.controller.login_user is not None:
                if self.controller.login_user["is_admin"]: # Giriş yapan kullanıcı admin ise admin sayfasına yönlendir
                    print("Admin Kullanıcısı Giriş Yaptı")
                    self.controller.show_frame("AdminPage")
                else:
                    self.controller.show_frame("MenuPage")# Giriş yapan kullanıcı admin değil ise menü sayfasına yönlendir

# Kayıt olma sayfasının sınıfı
class RegisterPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller

        label = tk.Label(self, text="Kayıt Ol", font=("Helvetica", 16), bg=bg_color, fg="white")
        label.pack(pady=100)

        name_entry = PlaceholderEntry(self, "İsim Soyisim", width=30)
        name_entry.place(x="195px", y="160")

        email_entry = PlaceholderEntry(self, "E-posta", width=30)
        email_entry.place(x="195px", y="200")

        password_entry = PlaceholderEntry(self, "Parola", width=30)
        password_entry.place(x="195px", y="240")

        login_button = tk.Button(self, text="Kayıt Ol", command=lambda: self.RegisterCheck(name_entry.get(), email_entry.get(), password_entry.get()), width=16, bg="white", fg="black")
        login_button.place(x="220px", y="280")

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("HomePage"), width=16, bg="white", fg="black")
        back_button.place(x="220px", y="310")

    # Kayıt ol butonuna basınca çalışacak fonksiyon
    def RegisterCheck(self, name, email, password):
        name = str(name).strip().replace("İsim Soyisim", "").capitalize()
        email = str(email).strip().replace("E-posta", "")
        password = str(password).strip().replace("Parola", "")
        if len(name) <= 0 and len(email) <= 0 and len(password) <= 0: # Uzunluk kontrolü ile boş veri gelmesini engelle
            print("Lütfen tüm boşlukları doldurunuz")
        else:
            result = AddUser(email, password, name) # Kullanıcı ekleme fonksiyonu ile kullanıyı ekle
            if result[0]:
                print("Kayıt Olundu")
                self.controller.show_frame("LoginPage") # Kayıt işlemi tamamlandıktan sonra Giriş sayfasına yönelendir
            else:
                print(result[1])

# Menü sayfasının sınıfı
class MenuPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller

        self.menu_label = tk.Label(self, text=f"Hoşgeldiniz", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.menu_label.place(x="160px", y="20px")

        account_exit_button = tk.Button(self, text="Hesaptan Çık", width=10, bg="White", fg="black", height=1, command=self.logout)
        account_exit_button.place(x="450px", y="20px")

        food_menu_button = tk.Button(self, text="Yemekler", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("FoodsPage"))
        food_menu_button.place(x="130px", y="100px")

        dessert_menu_button = tk.Button(self, text="Tatlılar", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("DessertsPage"))
        dessert_menu_button.place(x="230px", y="100px")

        drink_menu_button = tk.Button(self, text="İçecekler", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("DrinksPage"))
        drink_menu_button.place(x="330px", y="100px")

        self.label = tk.Label(self, text=f"Sepet", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.label.place(x="250px", y="150px")

        # Sepetimizdeki ürünleri listelemek için tkinterın tablo yapısı
        self.cart_treeview = ttk.Treeview(self, columns=("ID", "Ürün", "Tür", "Adet", "Fiyat"), show="headings")
        self.cart_treeview.heading("ID", text="ID")
        self.cart_treeview.heading("Ürün", text="Ürün")
        self.cart_treeview.heading("Tür", text="Tür")
        self.cart_treeview.heading("Adet", text="Adet")
        self.cart_treeview.heading("Fiyat", text="Fiyat")

        self.cart_treeview.column("ID", width=50)
        self.cart_treeview.column("Ürün", width=150)
        self.cart_treeview.column("Tür", width=100)
        self.cart_treeview.column("Adet", width=50)
        self.cart_treeview.column("Fiyat", width=50)

        # Tabloyu konumlandır ve boyutlandır
        self.cart_treeview.place(x="25px", y="190px", width=639, height=160)

        delete_product_button = tk.Button(self, text="Ürünü Sil", command=self.delete_product, width=45, bg="White", fg="black", height=1)
        delete_product_button.place(x="25px", y="315px")

        buy_button = tk.Button(self, text="Öde", command=self.buy_basket, width=43, bg="White", fg="black", height=1)
        buy_button.place(x="270px", y="315px")

    # Çıkış butonuna basılırsa çalışacak fonksiyon
    def logout(self):
        self.controller.login_user = None
        self.controller.cart = []
        self.controller.receipt = ""
        self.controller.show_frame("HomePage")# Tüm bilgiler sıfırlandıktan sonra Anasayfaya döndür

    # Öde butonuna basılınca çalışacak fonksiyon
    def buy_basket(self):
        if len(self.controller.cart) > 0: # Sepette ürün var ise çalış
            ReceiptFile = CreateReceipt(self.controller.cart, self.controller.login_user["id"]) # CreateReceipt Fonksiyonu ile fiş oluşturuldu
            self.controller.receipt = ReceiptFile
            self.controller.cart = []
            self.controller.show_frame("ReceiptPage") # Fiş görüntüleme sayfasına yönelendir
    
    # Ürünü sil butonuna basılınca çalışacak fonksiyon
    def delete_product(self):
        selected_item = self.cart_treeview.selection() # Seçilen ürünü kaydet
        if selected_item:
            item = self.cart_treeview.item(selected_item)
            item_id = item["values"][0]
            self.cart_treeview.delete(selected_item)  # Tablodan ürünü sil
            self.controller.cart = [product for product in self.controller.cart if product["id"] != item_id] # Sepetten ürünü sil

    # Sayfa her yüklendiğinde çalışacak fonksiyon
    def load_page(self):
        if self.controller.login_user: # Kullanıcı girişi yapıldı ise label'ı değiştir
            user_info = f"Hoşgeldiniz, {self.controller.login_user['full_name']}"
            self.menu_label.config(text=user_info)

        
        self.cart_treeview.delete(*self.cart_treeview.get_children())
        for item in self.controller.cart: # Sepetteki ürünleri güncelle
            self.cart_treeview.insert("", "end", values=(item["id"], item["product"], item["variant"], item["quantity"], item["price"]))


# Yemekler sayfasının sınıfı
class FoodsPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller

        self.selected_food = None

        # Tüm yemekleri çek
        foods = ReadProducts()

        label = tk.Label(self, text="Yemekler", font=("Helvetica", 16), bg=bg_color, fg="white")
        label.pack(pady=20)

        self.create_food_buttons(foods)

        control_frame = tk.Frame(self, bg=bg_color)
        control_frame.pack(pady=10)

        self.variety_combobox = ttk.Combobox(control_frame, state="readonly")
        self.variety_combobox.grid(row=0, column=0, padx=5)

        self.piece_entry = tk.Entry(control_frame, width=5)
        self.piece_entry.insert(0, "1")
        self.piece_entry.grid(row=0, column=1, padx=5)

        self.add_to_cart_button = tk.Button(control_frame, text="Sepete Ekle", command=self.add_to_cart, bg="white", fg="black")
        self.add_to_cart_button.grid(row=0, column=2, padx=5)

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("MenuPage"), width=90, bg="white", fg="black")
        back_button.pack(side=tk.BOTTOM, pady=20)


    # Yemek seçildiğinde yemeğin varyasyonu var ise komboboxa ekleyen fonksiyon
    def show_varieties(self, food):
        self.selected_food = food
        if food['is_variety']:
            varieties = [f"{variety['name']} (+{variety['add_price']} TL)" for variety in food['variety']]
            self.variety_combobox['values'] = varieties
            self.variety_combobox.current(0)
            self.variety_combobox.config(state="readonly")
        else:
            self.variety_combobox['values'] = []
            self.variety_combobox.set('')
            self.variety_combobox.config(state="disabled")

    # Yemeklere göre dinamik olarak butonları oluşturacak fonksiyon
    def create_food_buttons(self, foods):
        buttons_frame = tk.Frame(self, bg=self['bg'])
        buttons_frame.pack(pady=10)

        for idx, food in enumerate(foods):
            button = tk.Button(buttons_frame, text=food['name'], command=lambda f=food: self.show_varieties(f), width=20, height=3, bg="white", fg="black")
            button.grid(row=idx // 3, column=idx % 3, padx=10, pady=10)

    # Sepete ekle butonuna basınca çalışacak fonksiyon
    def add_to_cart(self):
        if self.selected_food:
            piece = self.piece_entry.get()
            if piece.isdigit(): # Girilen adetin numeric olup olmadığı kontrol ediliyor
                piece = int(piece)
                if piece > 0:
                    if len(self.controller.cart) > 0:
                        max_id = max(item["id"] for item in self.controller.cart) # Eğer sepette ürün var ise en yüksek id li ürün seçilip yeni id oluşturuluyor
                        new_id = max_id + 1
                    else:
                        new_id = 1

                    price = self.selected_food["price"]
                    if self.selected_food["is_variety"]: # Ürünün varyasyonu var ise ona göre sepete ekleniyor
                        new_price = self.variety_combobox.get().split("+")[1]
                        new_price = float(new_price.split(" ")[0] ) + price
                        data = {"id": new_id, "product": self.selected_food["name"], "variant": self.variety_combobox.get(), "quantity": piece, "price" : new_price}
                    else:
                        data = {"id": new_id, "product": self.selected_food["name"], "variant": self.variety_combobox.get(), "quantity": piece, "price" : price}

                    self.controller.cart.append(data)
                    
# Tatlılar sayfasının sınıfı
class DessertsPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)  # Arka plan rengini burada ayarlayın
        self.controller = controller

        label = tk.Label(self, text="Tatlılar", font=("Helvetica", 16), bg=bg_color, fg="white")
        label.pack(pady=20)

        desserts = ReadProducts(2)

        self.create_dessert_buttons(desserts)

        control_frame = tk.Frame(self, bg=bg_color)
        control_frame.pack(pady=10)

        self.variety_combobox = ttk.Combobox(control_frame, state="readonly")
        self.variety_combobox.grid(row=0, column=0, padx=5)

        self.piece_entry = tk.Entry(control_frame, width=5)
        self.piece_entry.insert(0, "1")
        self.piece_entry.grid(row=0, column=1, padx=5)

        self.add_to_cart_button = tk.Button(control_frame, text="Sepete Ekle", command=self.add_to_cart, bg="white", fg="black")
        self.add_to_cart_button.grid(row=0, column=2, padx=5)

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("MenuPage"), width=90, bg="white", fg="black")
        back_button.pack(side=tk.BOTTOM, pady=20)

    
    def create_dessert_buttons(self, desserts):
        buttons_frame = tk.Frame(self, bg=self['bg'])
        buttons_frame.pack(pady=10)

        for idx, dessert in enumerate(desserts):
            button = tk.Button(buttons_frame, text=dessert['name'], command=lambda f=dessert: self.show_varieties(f), width=20, height=3, bg="white", fg="black")
            button.grid(row=idx // 3, column=idx % 3, padx=10, pady=10)

    def show_varieties(self, dessert):
        self.selected_dessert = dessert
        if dessert['is_variety']:
            varieties = [f"{variety['name']} (+{variety['add_price']} TL)" for variety in dessert['variety']]
            self.variety_combobox['values'] = varieties
            self.variety_combobox.current(0)
            self.variety_combobox.config(state="readonly")
        else:
            self.variety_combobox['values'] = []
            self.variety_combobox.set('')
            self.variety_combobox.config(state="disabled")

    def add_to_cart(self):
        if self.selected_dessert:
            piece = self.piece_entry.get()
            if piece.isdigit():
                piece = int(piece)
                if piece > 0:
                    if len(self.controller.cart) > 0:
                        max_id = max(item["id"] for item in self.controller.cart)
                        new_id = max_id + 1
                    else:
                        new_id = 1

                    price = self.selected_dessert["price"]
                    if self.selected_dessert["is_variety"]:
                        new_price = self.variety_combobox.get().split("+")[1]
                        new_price = float(new_price.split(" ")[0] ) + price
                        data = {"id": new_id, "product": self.selected_dessert["name"], "variant": self.variety_combobox.get(), "quantity": piece, "price" : new_price}
                    else:
                        data = {"id": new_id, "product": self.selected_dessert["name"], "variant": self.variety_combobox.get(), "quantity": piece, "price" : price}

                    self.controller.cart.append(data)

# İÇecekler sayfasının sınıfı
class DrinksPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)  # Arka plan rengini burada ayarlayın
        self.controller = controller

        label = tk.Label(self, text="İçecekler", font=("Helvetica", 16), bg=bg_color, fg="white")
        label.pack(pady=20)

        drinks = ReadProducts(3)

        self.create_drink_buttons(drinks)

        control_frame = tk.Frame(self, bg=bg_color)
        control_frame.pack(pady=10)

        self.size_combobox = ttk.Combobox(control_frame, state="readonly")
        self.size_combobox.grid(row=0, column=0, padx=5)

        self.piece_entry = tk.Entry(control_frame, width=5)
        self.piece_entry.insert(0, "1")
        self.piece_entry.grid(row=0, column=1, padx=5)

        self.add_to_cart_button = tk.Button(control_frame, text="Sepete Ekle", command=self.add_to_cart, bg="white", fg="black")
        self.add_to_cart_button.grid(row=0, column=2, padx=5)

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("MenuPage"), width=90, bg="white", fg="black")
        back_button.pack(side=tk.BOTTOM, pady=20)

    def create_drink_buttons(self, drinks):
        buttons_frame = tk.Frame(self, bg=self['bg'])
        buttons_frame.pack(pady=10)

        for idx, drink in enumerate(drinks):
            button = tk.Button(buttons_frame, text=drink['name'], command=lambda f=drink: self.show_sizes(f), width=20, height=3, bg="white", fg="black")
            button.grid(row=idx // 3, column=idx % 3, padx=10, pady=10)

    def show_sizes(self, drink):
        self.selected_drink = drink
        if drink['is_size']:
            varieties = [f"{size['name']} (+{size['add_price']} TL)" for size in drink['size']]
            self.size_combobox['values'] = varieties
            self.size_combobox.current(0)
            self.size_combobox.config(state="readonly")
        else:
            self.size_combobox['values'] = []
            self.size_combobox.set('')
            self.size_combobox.config(state="disabled")

    def add_to_cart(self):
        if self.selected_drink:
            piece = self.piece_entry.get()
            if piece.isdigit():
                piece = int(piece)
                if piece > 0:
                    if len(self.controller.cart) > 0:
                        max_id = max(item["id"] for item in self.controller.cart)
                        new_id = max_id + 1
                    else:
                        new_id = 1

                    price = self.selected_drink["price"]
                    if self.selected_drink["is_size"]:
                        new_price = self.size_combobox.get().split("+")[1]
                        new_price = float(new_price.split(" ")[0] ) + price
                        data = {"id": new_id, "product": self.selected_drink["name"], "variant": self.size_combobox.get(), "quantity": piece, "price" : new_price}
                    else:
                        data = {"id": new_id, "product": self.selected_drink["name"], "variant": self.size_combobox.get(), "quantity": piece, "price" : price}

                    self.controller.cart.append(data)

# Fiş görüntüleme sayfası
class ReceiptPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller
        self.viewer = None

        #Canvas sınıfı oluştur
        self.canvas = tk.Canvas(self, width=600, height=400)
        self.canvas.pack()

        self.back_button = tk.Button(self, text="Geri", height=2, width=90, command=lambda: controller.show_frame("MenuPage"))
        self.back_button.pack(side="bottom", pady=10)

    def load_page(self):
        if self.viewer:
            self.viewer.destroy()

        pdf_path = self.controller.receipt
        if not os.path.exists(pdf_path):# Pdf in dosya yolu kontrol ediliyor eğer yok ise devam etmiyor
            print(f"Dosya bulunamadı: {pdf_path}")
            return

        self.pdf_document = fitz.open(pdf_path)
        self.current_page = 0
        self.total_pages = len(self.pdf_document)

        self.show_page(self.current_page)

        self.bind("<Left>", self.previous_page)
        self.bind("<Right>", self.next_page)
        self.bind("<Up>", self.previous_page)
        self.bind("<Down>", self.next_page)

    # Pdfin içeriği canvas ile ekrana getiren fonksiyon
    def show_page(self, page_number):
        page = self.pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        
        self.photo = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
    def next_page(self, event=None):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page(self.current_page)
            
    def previous_page(self, event=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

# Admin sayfası sınıfı
class AdminPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller
        self.menu_label = tk.Label(self, text=f"Admin Paneli", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.menu_label.place(x="200px", y="20px")

        account_exit_button = tk.Button(self, text="Hesaptan Çık", width=10, bg="White", fg="black", height=1, command=self.logout)
        account_exit_button.place(x="450px", y="20px")

        food_menu_button = tk.Button(self, text="Yemek Ekle/Sil", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("FoodAddPage"))
        food_menu_button.place(x="130px", y="100px")

        dessert_menu_button = tk.Button(self, text="Tatlı Ekle/Sil", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("DessertAddPage"))
        dessert_menu_button.place(x="230px", y="100px")

        drink_menu_button = tk.Button(self, text="İçecek Ekle/Sil", width=13, bg="White", fg="black", height=2, command=lambda: controller.show_frame("DrinkAddPage"))
        drink_menu_button.place(x="330px", y="100px")

    def logout(self):
        self.controller.login_user = None
        self.controller.cart = []
        self.controller.receipt = ""
        self.controller.show_frame("HomePage")

# Yemek ekleme sayfası sınıfı
class FoodAddPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller
        self.menu_label = tk.Label(self, text=f"Yemek Ekle/Sil", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.menu_label.place(x="200px", y="20px")

        self.food_name_entry = PlaceholderEntry(self, "Yemek Adı", width=30)
        self.food_name_entry.place(x="20px", y="100")

        self.food_price_entry = PlaceholderEntry(self, "Yemek Fiyatı", width=30)
        self.food_price_entry.place(x="20px", y="130")

        add_button = tk.Button(self, text="Kaydet", command=self.add_food, width=25, bg="white", fg="black")
        add_button.place(x="20px", y="155")

        self.variety_name_entry = PlaceholderEntry(self, "Varyasyon Adı", width=30)
        self.variety_name_entry.place(x="161px", y="100")

        self.variety_price_entry = PlaceholderEntry(self, "Varyasyon Fiyatı", width=30)
        self.variety_price_entry.place(x="161px", y="130")

        add_variety_button = tk.Button(self, text="Varyasyon Ekle", command=self.add_variety, width=25, bg="white", fg="black")
        add_variety_button.place(x="161px", y="155")

        delete_variety_button = tk.Button(self, text="Varyasyon Sil", command=self.delete_variety, width=25, bg="white", fg="black")
        delete_variety_button.place(x="161px", y="185")

        self.food_variet_treeview = ttk.Treeview(self, columns=("ID", "Varyasyon", "Fiyat"), show="headings")
        self.food_variet_treeview.heading("ID", text="ID")
        self.food_variet_treeview.heading("Varyasyon", text="Ürün")
        self.food_variet_treeview.heading("Fiyat", text="Varyasyon")

        self.food_variet_treeview.column("ID", width=50)
        self.food_variet_treeview.column("Varyasyon", width=100)
        self.food_variet_treeview.column("Fiyat", width=50)

        self.food_variet_treeview.place(x="302px", y="75px", width=276, height=120)


        self.label = tk.Label(self, text=f"Kayıtlı Yemekler", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.label.place(x="200px", y="165px")

        self.food_treeview = ttk.Treeview(self, columns=("ID", "Ürün", "Varyasyon"), show="headings")
        self.food_treeview.heading("ID", text="ID")
        self.food_treeview.heading("Ürün", text="Ürün")
        self.food_treeview.heading("Varyasyon", text="Varyasyon")

        self.food_treeview.column("ID", width=50)
        self.food_treeview.column("Ürün", width=150)
        self.food_treeview.column("Varyasyon", width=100)

        self.food_treeview.place(x="25px", y="190px", width=447, height=160)
        self.food_treeview.bind("<ButtonRelease-1>", self.on_treeview_click)

        self.variety_combo = ttk.Combobox(self, state="readonly")
        self.variety_combo.place(x="361px", y="190px", width=200)

        delete_product_button = tk.Button(self, text="Ürünü Sil", command=self.delete_product, width=30, bg="White", fg="black", height=1)
        delete_product_button.place(x="25px", y="315px")

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("AdminPage"), width=30, bg="white", fg="black")
        back_button.place(x="195px", y="315px")

    # Yemek ekle butonuna basıldığında çalışacak fonskiyon
    def add_food(self):
        if len(self.food_name_entry.get()) > 0:
            price = self.food_price_entry.get()
            if price.isdigit() and int(price) >= 0:
                foods = ReadProducts(1)

                max_id = max([food["id"] for food in foods])
                new_id = max_id + 1

                is_variety = False
                varieties = self.food_variet_treeview.get_children()
                if varieties: # Eğer varyasyon eklendiyse varyasyon listesi oluşturulacak
                    is_variety = True
                    variety_list = []
                    for variety in varieties:
                        values = self.food_variet_treeview.item(variety)["values"]
                        varr = {"name" : values[1], "add_price" : int(values[2])}
                        variety_list.append(varr)
                else:
                    variety_list = [] # Varyasyon eklenmediği için liste boş tanımlanıyor

                new_food = {
                    "id": new_id,
                    "name": self.food_name_entry.get().capitalize(),
                    "is_variety": is_variety,
                    "variety": variety_list,
                    "price": int(price)
                }

                foods.append(new_food) # Yemekler değişkenine yeni yemek ekliyerek güncelliyoruz
                with open('./products/foods.json', 'w', encoding="utf8") as f:
                    json.dump(foods, f, indent=4)
                
                self.controller.show_frame("FoodAddPage")

    # Varyasyonu tabloya ekliyecek fonksiyon
    def add_variety(self):
        if len(self.variety_name_entry.get()) > 0:
            price = self.variety_price_entry.get()
            if price.isdigit() and int(price) > 0: # Gerekli kontroller yapıldı
                if not self.food_variet_treeview.get_children(): # tabloda eleman varmı yokmu kontrol ediliyor yok ise id 1 veriliyor var ise en yüksek id değeri + 1 ile yeni id oluşturuluyor
                    new_id = 1
                else:
                    # Tüm elemanların id si alınıyor
                    ids = [int(self.food_variet_treeview.item(item, "values")[0]) for item in self.food_variet_treeview.get_children()]
                    max_id = max(ids)
                    new_id = max_id + 1

                self.food_variet_treeview.insert("", "end", values=(new_id, self.variety_name_entry.get(), price))
    # Tabloda elamana tıklanınca çalışacak fonksiyon
    def on_treeview_click(self,vevent):
        foods = ReadProducts(1)
        item = self.food_treeview.selection()[0]
        item_id = self.food_treeview.item(item, "values")[0]
        for food in foods:
            if food["id"] == int(item_id): # elemanın varlığı kontrol ediliyor
                if food['is_variety']:# eğer bu elemanın varyasyonları var ise kombobox dolduruluyor
                    varieties = [f"{variety['name']} (+{variety['add_price']} TL)" for variety in food['variety']]
                    self.variety_combo['values'] = varieties
                    self.variety_combo.current(0)
                    self.variety_combo.config(state="readonly")
                else:
                    self.variety_combo['values'] = []
                    self.variety_combo.set('')
                    self.variety_combo.config(state="disabled")

    def load_page(self):
        foods = ReadProducts(1)
        self.food_treeview.delete(*self.food_treeview.get_children())
        for food in foods:
            variety = "Yok"
            if food["is_variety"]:
                variety = "Var"
            self.food_treeview.insert("", "end", values=(food["id"], food["name"], variety))
    # Tabloda seçilen ürünü silen fonksiyon
    def delete_product(self):
        selected_item = self.food_treeview.selection()
        if selected_item:
            item = self.food_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün id sini al
            self.food_treeview.delete(selected_item) # seçilen ürünü tablodan sil

            # Ürünü Jsondan sileceğimiz kısım
            foods = ReadProducts(1)
            filtered_foods = [food for food in foods if food['id'] != item_id] # Ürün datadan silinerek güncel data dosyaya yazdırılıyor
            with open('./products/foods.json', 'w', encoding="utf8") as file:
                json.dump(filtered_foods, file, indent=4)

    def delete_variety(self):
        selected_item = self.food_variet_treeview.selection()
        if selected_item:
            item = self.food_variet_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün ID'sini al
            self.food_variet_treeview.delete(selected_item)

# Tatlı ekleme sayfası sınıfı
class DessertAddPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller
        self.menu_label = tk.Label(self, text=f"Tatlı Ekle/Sil", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.menu_label.place(x="200px", y="20px")

        self.dessert_name_entry = PlaceholderEntry(self, "Tatlı Adı", width=30)
        self.dessert_name_entry.place(x="20px", y="100")

        self.dessert_price_entry = PlaceholderEntry(self, "Tatlı Fiyatı", width=30)
        self.dessert_price_entry.place(x="20px", y="130")

        add_button = tk.Button(self, text="Kaydet", command=self.add_dessert, width=25, bg="white", fg="black")
        add_button.place(x="20px", y="155")

        self.variety_name_entry = PlaceholderEntry(self, "Varyasyon Adı", width=30)
        self.variety_name_entry.place(x="161px", y="100")

        self.variety_price_entry = PlaceholderEntry(self, "Varyasyon Fiyatı", width=30)
        self.variety_price_entry.place(x="161px", y="130")

        add_variety_button = tk.Button(self, text="Varyasyon Ekle", command=self.add_variety, width=25, bg="white", fg="black")
        add_variety_button.place(x="161px", y="155")

        delete_variety_button = tk.Button(self, text="Varyasyon Sil", command=self.delete_variety, width=25, bg="white", fg="black")
        delete_variety_button.place(x="161px", y="185")

        self.dessert_variet_treeview = ttk.Treeview(self, columns=("ID", "Varyasyon", "Fiyat"), show="headings")
        self.dessert_variet_treeview.heading("ID", text="ID")
        self.dessert_variet_treeview.heading("Varyasyon", text="Ürün")
        self.dessert_variet_treeview.heading("Fiyat", text="Varyasyon")

        self.dessert_variet_treeview.column("ID", width=50)
        self.dessert_variet_treeview.column("Varyasyon", width=100)
        self.dessert_variet_treeview.column("Fiyat", width=50)

        self.dessert_variet_treeview.place(x="302px", y="75px", width=276, height=120)


        self.label = tk.Label(self, text=f"Kayıtlı Tatlılar", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.label.place(x="200px", y="165px")

        self.dessert_treeview = ttk.Treeview(self, columns=("ID", "Ürün", "Varyasyon"), show="headings")
        self.dessert_treeview.heading("ID", text="ID")
        self.dessert_treeview.heading("Ürün", text="Ürün")
        self.dessert_treeview.heading("Varyasyon", text="Varyasyon")

        self.dessert_treeview.column("ID", width=50)
        self.dessert_treeview.column("Ürün", width=150)
        self.dessert_treeview.column("Varyasyon", width=100)

        self.dessert_treeview.place(x="25px", y="190px", width=447, height=160)
        self.dessert_treeview.bind("<ButtonRelease-1>", self.on_treeview_click)

        self.variety_combo = ttk.Combobox(self, state="readonly")
        self.variety_combo.place(x="361px", y="190px", width=200)

        delete_product_button = tk.Button(self, text="Ürünü Sil", command=self.delete_product, width=30, bg="White", fg="black", height=1)
        delete_product_button.place(x="25px", y="315px")

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("AdminPage"), width=30, bg="white", fg="black")
        back_button.place(x="195px", y="315px")

    def add_dessert(self):
        if len(self.dessert_name_entry.get()) > 0:
            price = self.dessert_price_entry.get()
            if price.isdigit() and int(price) > 0:
                desserts = ReadProducts(2)

                max_id = max([dessert["id"] for dessert in desserts])
                new_id = max_id + 1

                is_variety = False
                varieties = self.dessert_variet_treeview.get_children()
                if varieties:
                    is_variety = True
                    variety_list = []
                    for variety in varieties:
                        values = self.dessert_variet_treeview.item(variety)["values"]
                        varr = {"name" : values[1], "add_price" : int(values[2])}
                        variety_list.append(varr)
                else:
                    variety_list = []

                new_food = {
                    "id": new_id,
                    "name": self.dessert_name_entry.get().capitalize(),
                    "is_variety": is_variety,
                    "variety": variety_list,
                    "price": int(price)
                }

                desserts.append(new_food)
                with open('./products/desserts.json', 'w', encoding="utf8") as f:
                    json.dump(desserts, f, indent=4)
                
                self.controller.show_frame("DessertAddPage")

    def on_treeview_click(self,vevent):
        desserts = ReadProducts(2)
        item = self.dessert_treeview.selection()[0]
        item_id = self.dessert_treeview.item(item, "values")[0]
        for dessert in desserts:
            if dessert["id"] == int(item_id):
                if dessert['is_variety']:
                    varieties = [f"{variety['name']} (+{variety['add_price']} TL)" for variety in dessert['variety']]
                    self.variety_combo['values'] = varieties
                    self.variety_combo.current(0)
                    self.variety_combo.config(state="readonly")
                else:
                    self.variety_combo['values'] = []
                    self.variety_combo.set('')
                    self.variety_combo.config(state="disabled")

    def add_variety(self):
        if len(self.variety_name_entry.get()) > 0:
            price = self.variety_price_entry.get()
            if price.isdigit() and int(price) >= 0:
                if not self.dessert_variet_treeview.get_children():
                    new_id = 1
                else:
                    # Tüm item'ların ID'lerini al
                    ids = [int(self.dessert_variet_treeview.item(item, "values")[0]) for item in self.dessert_variet_treeview.get_children()]
                    # En yüksek ID'yi bul
                    max_id = max(ids)
                    # Yeni ID'yi oluştur
                    new_id = max_id + 1

                self.dessert_variet_treeview.insert("", "end", values=(new_id, self.variety_name_entry.get(), price))

    def delete_variety(self):
        selected_item = self.dessert_variet_treeview.selection()
        if selected_item:
            item = self.dessert_variet_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün ID'sini al
            self.dessert_variet_treeview.delete(selected_item)

    def delete_product(self):
        selected_item = self.dessert_treeview.selection()
        if selected_item:
            item = self.dessert_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün ID'sini al
            self.dessert_treeview.delete(selected_item)

            # Ürünü Jsondan sileceğimiz kısım
            # self.controller.cart = [product for product in self.controller.cart if product["id"] != item_id]
            desserts = ReadProducts(2)
            filtered_desserts = [dessert for dessert in desserts if dessert['id'] != item_id]
            with open('./products/desserts.json', 'w', encoding="utf8") as file:
                json.dump(filtered_desserts, file, indent=4)

    def load_page(self):
        desserts = ReadProducts(2)
        self.dessert_treeview.delete(*self.dessert_treeview.get_children())
        for dessert in desserts:
            variety = "Yok"
            if dessert["is_variety"]:
                variety = "Var"
            self.dessert_treeview.insert("", "end", values=(dessert["id"], dessert["name"], variety))

# İçecek ekleme sayfası sınıfı
class DrinkAddPage(tk.Frame):
    def __init__(self, parent, controller, bg_color):
        super().__init__(parent, bg=bg_color)
        self.controller = controller
        self.menu_label = tk.Label(self, text=f"İçecek Ekle/Sil", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.menu_label.place(x="200px", y="20px")

        self.drink_name_entry = PlaceholderEntry(self, "İçecek Adı", width=30)
        self.drink_name_entry.place(x="20px", y="100")

        self.drink_price_entry = PlaceholderEntry(self, "İçecek Fiyatı", width=30)
        self.drink_price_entry.place(x="20px", y="130")

        add_button = tk.Button(self, text="Kaydet", command=self.add_drink, width=25, bg="white", fg="black")
        add_button.place(x="20px", y="155")

        self.variety_name_entry = PlaceholderEntry(self, "Varyasyon Adı", width=30)
        self.variety_name_entry.place(x="161px", y="100")

        self.variety_price_entry = PlaceholderEntry(self, "Varyasyon Fiyatı", width=30)
        self.variety_price_entry.place(x="161px", y="130")

        add_variety_button = tk.Button(self, text="Varyasyon Ekle", command=self.add_variety, width=25, bg="white", fg="black")
        add_variety_button.place(x="161px", y="155")

        delete_variety_button = tk.Button(self, text="Varyasyon Sil", command=self.delete_variety, width=25, bg="white", fg="black")
        delete_variety_button.place(x="161px", y="185")

        self.drink_variet_treeview = ttk.Treeview(self, columns=("ID", "Varyasyon", "Fiyat"), show="headings")
        self.drink_variet_treeview.heading("ID", text="ID")
        self.drink_variet_treeview.heading("Varyasyon", text="Ürün")
        self.drink_variet_treeview.heading("Fiyat", text="Varyasyon")

        self.drink_variet_treeview.column("ID", width=50)
        self.drink_variet_treeview.column("Varyasyon", width=100)
        self.drink_variet_treeview.column("Fiyat", width=50)

        self.drink_variet_treeview.place(x="302px", y="75px", width=276, height=120)


        self.label = tk.Label(self, text=f"Kayıtlı Tatlılar", font=("Helvetica", 16), bg=bg_color, fg="white")
        self.label.place(x="200px", y="165px")

        self.drink_treeview = ttk.Treeview(self, columns=("ID", "Ürün", "Varyasyon"), show="headings")
        self.drink_treeview.heading("ID", text="ID")
        self.drink_treeview.heading("Ürün", text="Ürün")
        self.drink_treeview.heading("Varyasyon", text="Varyasyon")

        self.drink_treeview.column("ID", width=50)
        self.drink_treeview.column("Ürün", width=150)
        self.drink_treeview.column("Varyasyon", width=100)

        self.drink_treeview.place(x="25px", y="190px", width=447, height=160)
        self.drink_treeview.bind("<ButtonRelease-1>", self.on_treeview_click)

        self.variety_combo = ttk.Combobox(self, state="readonly")
        self.variety_combo.place(x="361px", y="190px", width=200)

        delete_product_button = tk.Button(self, text="Ürünü Sil", command=self.delete_product, width=30, bg="White", fg="black", height=1)
        delete_product_button.place(x="25px", y="315px")

        back_button = tk.Button(self, text="Geri", command=lambda: controller.show_frame("AdminPage"), width=30, bg="white", fg="black")
        back_button.place(x="195px", y="315px")


    def add_drink(self):
        if len(self.drink_name_entry.get()) > 0:
            price = self.drink_price_entry.get()
            if price.isdigit() and int(price) > 0:
                drinks = ReadProducts(3)

                max_id = max([drink["id"] for drink in drinks])
                new_id = max_id + 1

                is_variety = False
                varieties = self.drink_variet_treeview.get_children()
                if varieties:
                    is_variety = True
                    variety_list = []
                    for variety in varieties:
                        values = self.drink_variet_treeview.item(variety)["values"]
                        varr = {"name" : values[1], "add_price" : int(values[2])}
                        variety_list.append(varr)
                else:
                    variety_list = []

                new_food = {
                    "id": new_id,
                    "name": self.drink_name_entry.get().capitalize(),
                    "is_size": is_variety,
                    "size": variety_list,
                    "price": int(price)
                }

                drinks.append(new_food)
                with open('./products/drinks.json', 'w', encoding="utf8") as f:
                    json.dump(drinks, f, indent=4)
                
                self.controller.show_frame("DrinkAddPage")

    def on_treeview_click(self,vevent):
        drinks = ReadProducts(3)
        item = self.drink_treeview.selection()[0]
        item_id = self.drink_treeview.item(item, "values")[0]
        for drink in drinks:
            if drink["id"] == int(item_id):
                if drink['is_size']:
                    varieties = [f"{variety['name']} (+{variety['add_price']} TL)" for variety in drink['size']]
                    self.variety_combo['values'] = varieties
                    self.variety_combo.current(0)
                    self.variety_combo.config(state="readonly")
                else:
                    self.variety_combo['values'] = []
                    self.variety_combo.set('')
                    self.variety_combo.config(state="disabled")

    def add_variety(self):
        if len(self.variety_name_entry.get()) > 0:
            price = self.variety_price_entry.get()
            if price.isdigit() and int(price) >= 0:
                if not self.drink_variet_treeview.get_children():
                    new_id = 1
                else:
                    # Tüm item'ların ID'lerini al
                    ids = [int(self.drink_variet_treeview.item(item, "values")[0]) for item in self.drink_variet_treeview.get_children()]
                    # En yüksek ID'yi bul
                    max_id = max(ids)
                    # Yeni ID'yi oluştur
                    new_id = max_id + 1

                self.drink_variet_treeview.insert("", "end", values=(new_id, self.variety_name_entry.get(), price))

    def delete_variety(self):
        selected_item = self.drink_variet_treeview.selection()
        if selected_item:
            item = self.drink_variet_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün ID'sini al
            self.drink_variet_treeview.delete(selected_item)

    def delete_product(self):
        selected_item = self.drink_treeview.selection()
        if selected_item:
            item = self.drink_treeview.item(selected_item)
            item_id = item["values"][0]  # Seçili ürünün ID'sini al
            self.drink_treeview.delete(selected_item)

            # Ürünü Jsondan sileceğimiz kısım
            # self.controller.cart = [product for product in self.controller.cart if product["id"] != item_id]
            drinks = ReadProducts(3)
            filtered_drinks = [drink for drink in drinks if drink['id'] != item_id]
            with open('./products/drinks.json', 'w', encoding="utf8") as file:
                json.dump(filtered_drinks, file, indent=4)

    def load_page(self):
        drinks = ReadProducts(3)
        self.drink_treeview.delete(*self.drink_treeview.get_children())
        for drink in drinks:
            variety = "Yok"
            if drink["is_size"]:
                variety = "Var"
            self.drink_treeview.insert("", "end", values=(drink["id"], drink["name"], variety))
    
if __name__ == "__main__":
    app = RestaurantApp()
    app.mainloop()