# teknostres_app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import hashlib

# =========== AYARLAR ===========
st.set_page_config(page_title="Teknostres Ölçeği", page_icon="📱", layout="wide")

# max izin verilen katılım (aynı kimlik ile)
MAX_KATILIM = 2

# session state
if "email_verified" not in st.session_state:
    st.session_state["email_verified"] = True  # artık mail yok, her zaman True

# Basit CSS
st.markdown(
    """
    <style>
    .stButton>button { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📲 Teknostres Düzeyi Ölçme Uygulaması")
st.write("Bu form anonimdir. Veriler yalnızca akademik amaçlarla kullanılacaktır.")

def hash_kimlik(kimlik: str):
    return hashlib.sha256(kimlik.strip().lower().encode()).hexdigest()

# Sekmeler
tab_anket, tab_admin = st.tabs(["📝 Anket Formu", "🛠️ Admin Paneli"])

# ============== ANKET SEKME ==============
with tab_anket:
    st.header("🧾 Katılım Bilgisi")
    kimlik = st.text_input(
        "Lütfen e-posta adresiniz, öğrenci numaranız veya unutmayacağınız bir rumuz girin.\n"
        "Bu bilgi, aynı kişinin en fazla 2 kez katılım yapabilmesi için kullanılacaktır."
    )

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

        # 1) Kimlik girilmiş mi?
        if not kimlik:
            st.error("Lütfen kimlik (e-posta / öğrenci no / rumuz) alanını doldurun.")
            st.stop()

        kimlik_hash = hash_kimlik(kimlik)

        # 2) Daha önce bu kimlikle kaç kayıt var?
        if os.path.exists("veriler.csv"):
            df_existing = pd.read_csv("veriler.csv")
        else:
            df_existing = pd.DataFrame()

        if "KimlikHash" in df_existing.columns:
            onceki = (df_existing["KimlikHash"] == kimlik_hash).sum()
        else:
            onceki = 0

        if onceki >= MAX_KATILIM:
            st.error(f"Bu kimlikle zaten {MAX_KATILIM} kez katılım yapmışsınız. Daha fazla kayıt yapılamaz.")
            st.stop()

        # Teknostres düzeyini hesapla
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
            "Kimlik": [kimlik],
            "KimlikHash": [kimlik_hash],
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

# ============== ADMIN PANELİ ==============
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
