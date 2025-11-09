# teknostres_app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import random
import time
import hashlib

# E-posta gönderimi için
try:
    import yagmail
    YAG_AVAILABLE = True
except Exception:
    YAG_AVAILABLE = False

# ===========
# AYARLAR
# ===========
st.set_page_config(page_title="Teknostres Ölçeği | Doğrulamalı", page_icon="📱", layout="wide")

# E-posta gönderici bilgileri: Streamlit Cloud kullanıyorsan Settings -> Secrets içine ekle:
# {"SENDER_EMAIL": "youremail@gmail.com", "APP_PASSWORD": "16charapppass"}
SENDER_EMAIL = st.secrets["SENDER_EMAIL"] if "SENDER_EMAIL" in st.secrets else os.environ.get("SENDER_EMAIL")
APP_PASSWORD = st.secrets["APP_PASSWORD"] if "APP_PASSWORD" in st.secrets else os.environ.get("APP_PASSWORD")

# max izin verilen katılım (aynı email hash ile)
MAX_KATILIM = 2

# pending kodlar: session bazlı (kullanıcı aynı tarayıcıda kodu alıp doğrular)
if "pending_codes" not in st.session_state:
    st.session_state["pending_codes"] = {}  # email -> (kod, expiry_ts)

if "email_verified" not in st.session_state:
    st.session_state["email_verified"] = False

if "email_for_session" not in st.session_state:
    st.session_state["email_for_session"] = ""

# Küçük CSS
st.markdown(
    """
    <style>
    .stButton>button { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📲 Teknostres Düzeyi Ölçme (E-posta Doğrulamalı)")
st.write("Formu doldurmadan önce e-posta adresinize gönderilen kod ile doğrulama yapmanız gerekmektedir.")
if not YAG_AVAILABLE:
    st.warning("Not: `yagmail` yüklü değil. Eğer e-posta göndermek istiyorsanız `pip install yagmail` yapın.")

# Yardımcı fonksiyonlar
def gen_code():
    return f"{random.randint(100000, 999999)}"

def hash_email(email: str):
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()

def send_email_code(to_email: str, code: str):
    if not YAG_AVAILABLE:
        raise RuntimeError("yagmail kütüphanesi yüklü değil.")
    if not SENDER_EMAIL or not APP_PASSWORD:
        raise RuntimeError("E-posta ayarları eksik. SENDER_EMAIL ve APP_PASSWORD ayarlayın (secrets veya env).")
    yag = yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD)
    subject = "Teknostres Anketi - Doğrulama Kodunuz"
    contents = f"Merhaba,\n\nTeknostres anketi doğrulama kodunuz: {code}\nKod 5 dakika geçerlidir.\n\nTeşekkürler."
    yag.send(to=to_email, subject=subject, contents=contents)

# Sekmeler
tab_anket, tab_admin = st.tabs(["📝 Anket Formu", "🛠️ Admin Paneli"])

# ==============
# ANKET SEKME
# ==============
with tab_anket:
    st.header("📧 E-posta ile Doğrulama")

    email = st.text_input("E-posta adresinizi girin:", value=st.session_state.get("email_for_session", ""))
    col_send, col_resend = st.columns([1,1])
    with col_send:
        if st.button("📨 Kodu Gönder"):
            if not email:
                st.error("Lütfen geçerli bir e-posta adresi girin.")
            else:
                kod = gen_code()
                expiry = time.time() + 300  # 5 dakika
                st.session_state["pending_codes"][email] = (kod, expiry)
                st.session_state["email_for_session"] = email
                try:
                    send_email_code(email, kod)
                    st.success("Doğrulama kodu gönderildi — lütfen e-posta kutunuzu kontrol edin.")
                except Exception as e:
                    st.error(f"E-posta gönderilemedi: {e}")

    with col_resend:
        if st.button("🔁 Kodu Tekrar Gönder"):
            if not email or email not in st.session_state["pending_codes"]:
                st.warning("Önce e-posta adresinizi girip 'Kodu Gönder' butonuna basın.")
            else:
                kod, _ = st.session_state["pending_codes"][email]
                st.session_state["pending_codes"][email] = (kod, time.time() + 300)
                try:
                    send_email_code(email, kod)
                    st.success("Kod yeniden gönderildi.")
                except Exception as e:
                    st.error(f"E-posta gönderilemedi: {e}")

    kod_input = st.text_input("E-posta ile gelen 6 haneli kodu girin:")
    if st.button("🔐 Kodu Doğrula"):
        if not email:
            st.error("Önce e-posta girin.")
        elif email not in st.session_state["pending_codes"]:
            st.error("Bu e-posta için gönderilmiş bir kod yok. Lütfen önce 'Kodu Gönder' yapın.")
        else:
            kod, expiry = st.session_state["pending_codes"][email]
            if time.time() > expiry:
                st.error("Kodun süresi dolmuş. Lütfen yeniden kod isteyin.")
                del st.session_state["pending_codes"][email]
            elif kod_input.strip() == kod:
                st.success("✅ E-posta doğrulandı. Anketi doldurabilirsiniz.")
                st.session_state["email_verified"] = True
                # tek kullanımlık: sil
                del st.session_state["pending_codes"][email]
                st.session_state["email_for_session"] = email
            else:
                st.error("Kod yanlış. Lütfen tekrar kontrol edin.")

    if not st.session_state["email_verified"]:
        st.info("Kod doğrulanana kadar anket soru alanları gizlenecektir.")
    else:
        # ANKET FORMU (görünür)
        st.header("👤 Katılımcı Bilgileri")

        col1, col2 = st.columns(2)
        with col1:
            cinsiyet = st.selectbox("Cinsiyetiniz:", ["Kadın", "Erkek", "Diğer / Belirtmek istemiyorum"])
            yas = st.selectbox("Yaş Aralığınız:", ["18-21", "22-26", "27-35", "36-45", "46 ve üzeri"])
        with col2:
            bolum = st.text_input("Okuduğunuz Bölüm (örnek: Yönetim Bilişim Sistemleri)")

        st.subheader("👨‍👩‍👧 Aile Eğitimi")
        col3, col4 = st.columns(2)
        with col3:
            anne_okuryazar = st.selectbox("Anne okuryazarlığı:", [
                "Okuryazar değil", "İlkokul", "Ortaokul", "Lise", "Üniversite", "Yüksek Lisans / Doktora"
            ])
        with col4:
            baba_okuryazar = st.selectbox("Baba okuryazarlığı:", [
                "Okuryazar değil", "İlkokul", "Ortaokul", "Lise", "Üniversite", "Yüksek Lisans / Doktora"
            ])

        st.header("💻 Bildirim ve Teknoloji Kullanımı")
        col5, col6 = st.columns(2)
        with col5:
            ekran_suresi = st.selectbox("Günlük ortalama ekran süreniz (saat):", ["0-1", "2-5", "6-10", "10+"])
            bildirim_sayisi = st.selectbox("Günde ortalama kaç bildirim alıyorsunuz:", ["0-30", "31-60", "61-100", "100+"])
        with col6:
            bildirim_turu = st.selectbox("Hangi tür bildirimleri daha fazla alıyorsunuz:", [
                "Sosyal medya", "E-posta", "Oyun", "Haber", "Eğitim", "Diğer"
            ])
            cihaz = st.selectbox("En sık hangi cihazdan bildirim alıyorsunuz:", [
                "Telefon", "Tablet", "Bilgisayar", "Akıllı saat"
            ])

        st.header("🧠 Teknostres Düzeyi Soruları")
        st.write("Lütfen aşağıdaki ifadeleri 1 (Kesinlikle Katılmıyorum) ile 5 (Kesinlikle Katılıyorum) arasında puanlayın:")

        sorular = [
            ("S1", "Bildirimlerin sizi ne ölçüde etkilediğini düşünüyorsunuz?"),
            ("S2", "Bildirim geldiğinde dikkatinizin dağıldığını düşünüyor musunuz?"),
            ("S3", "Bildirimi hemen kontrol etme isteği hissediyorum."),
            ("S4", "Gelen bildirimleri yönetmekte zorlanıyorum."),
            ("S5", "Yeni teknolojileri öğrenmek beni strese sokuyor."),
            ("S6", "Bildirimleri kaçırmamak için sık sık cihazımı kontrol ediyorum."),
            ("S7", "Teknolojik hatalar (uygulama çökmesi, internet kesilmesi vb.) beni strese sokuyor."),
            ("S8", "İş/okul ile ilgili bildirimler özel hayatımı olumsuz etkiliyor."),
            ("S9", "Sürekli çevrimiçi olma baskısı hissediyorum."),
            ("S10", "Gün içinde teknolojiden uzak kalmakta zorlanıyorum."),
            ("S11", "Teknolojiyle ilgili yetersiz kaldığımı hissettiğim durumlar beni strese sokuyor."),
            ("S12", "Yeni teknolojik değişimlere ayak uydurmakta zorlandığımı hissediyorum.")
        ]

        puanlar = {}
        for kod, metin in sorular:
            puanlar[kod] = st.slider(f"{kod} - {metin}", 1, 5, 3)

        cevap_listesi = list(puanlar.values())
        ortalama = sum(cevap_listesi) / len(cevap_listesi)

        if st.button("🎯 Sonucu Göster ve Kaydet"):
            # e-posta doğrulandı mı kontrol (ek güvenlik)
            if not st.session_state.get("email_verified", False):
                st.error("E-posta doğrulanmadan kayıt yapılamaz.")
                st.stop()

            # e-posta hash ile max katılım kontrolü
            email_now = st.session_state.get("email_for_session", email)
            email_hash = hash_email(email_now)

            if os.path.exists("veriler.csv"):
                df_existing = pd.read_csv("veriler.csv")
            else:
                df_existing = pd.DataFrame()

            if "EmailHash" in df_existing.columns:
                önceki = (df_existing["EmailHash"] == email_hash).sum()
            else:
                önceki = 0

            if önceki >= MAX_KATILIM:
                st.error(f"Bu e-posta ile zaten {MAX_KATILIM} kez katılım yapmışsınız. Daha fazla kayıt yapılamaz.")
                st.stop()

            # düzey hesapla
            if ortalama < 2.5:
                düzey = "Düşük"
                renk = "🟢"
            elif ortalama < 3.5:
                düzey = "Orta"
                renk = "🟡"
            else:
                düzey = "Yüksek"
                renk = "🔴"

            st.subheader(f"{renk} Teknostres Düzeyiniz: {düzey}")
            st.write(f"Ortalama Puanınız: **{ortalama:.2f} / 5**")

            tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            data = {
                "Tarih": [tarih],
                "EmailHash": [email_hash],
                "Cinsiyet": [cinsiyet],
                "Yaş": [yas],
                "Bölüm": [bolum],
                "Anne Okuryazarlığı": [anne_okuryazar],
                "Baba Okuryazarlığı": [baba_okuryazar],
                "Ekran Süresi": [ekran_suresi],
                "Bildirim Sayısı": [bildirim_sayisi],
                "Bildirim Türü": [bildirim_turu],
                "Cihaz": [cihaz],
                "Ortalama": [ortalama],
                "Düzey": [düzey]
            }

            for kod, _ in sorular:
                data[kod] = [puanlar[kod]]

            df_new = pd.DataFrame(data)
            if not df_existing.empty:
                df_all = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_all = df_new
            df_all.to_csv("veriler.csv", index=False)

            st.success("✅ Cevabınız kaydedildi. Teşekkür ederiz!")

# ==============
# ADMIN PANELİ
# ==============
with tab_admin:
    st.header("🛠️ Admin Paneli")
    st.write("Bu bölüm yalnızca araştırmacı / yönetici içindir.")
    admin_sifre = st.text_input("Admin şifresi:", type="password")
    if admin_sifre == "1234":
        st.success("Admin girişi başarılı ✅")
        if os.path.exists("veriler.csv"):
            df = pd.read_csv("veriler.csv")
            st.subheader("📂 Kayıtlı Veriler")
            st.dataframe(df, use_container_width=True)
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Toplam Katılımcı", len(df))
            with col_b:
                st.metric("Genel Teknostres Ortalaması", f"{df['Ortalama'].mean():.2f}")
            with col_c:
                if "Cinsiyet" in df.columns:
                    cinsiyet_sayim = df["Cinsiyet"].value_counts().to_dict()
                    st.write("Cinsiyet Dağılımı:")
                    st.write(cinsiyet_sayim)
            st.subheader("📊 Cinsiyete Göre Ortalama Teknostres")
            if "Cinsiyet" in df.columns:
                grup_ortalama = df.groupby("Cinsiyet")["Ortalama"].mean().reset_index()
                st.bar_chart(data=grup_ortalama, x="Cinsiyet", y="Ortalama", use_container_width=True)
        else:
            st.warning("Henüz 'veriler.csv' dosyası oluşturulmadı.")
    elif admin_sifre != "":
        st.error("❌ Hatalı şifre. Yetkisiz erişim.")
