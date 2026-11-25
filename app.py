import base64, html, io, os
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import db
import importer
import icons
from icons import svg as ic

st.set_page_config(page_title="Nuru - Find your next opportunity", page_icon=":material/lightbulb:", layout="wide")
db.init()

PURPLE = "#6200B3"
CATEGORY_FALLBACK = ["Banks & Finance", "Medical", "Schools & Education", "NGOs & Development",
                     "Engineering & Construction", "ICT & Tech", "Agriculture", "Internships", "Other"]

# ------------------------------------------------------------------ styling
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {{ font-family: 'Poppins', sans-serif !important; }}
#MainMenu, footer, header[data-testid="stHeader"] {{ display: none; }}
.block-container {{ padding-top: 1rem; max-width: 1180px; }}
.logo {{ font-size: 1.5rem; font-weight: 700; color: {PURPLE}; padding-top: .35rem; }}
.hero {{ background: linear-gradient(135deg,#F3EAFF 0%,#FFFFFF 100%); border-radius: 18px; padding: 3rem 2.5rem 2rem; margin: .8rem 0 1.5rem; }}
.hero h1 {{ font-size: 2.4rem; font-weight: 600; color:#2B2B2B; line-height:1.25; margin:0 0 .4rem; }}
.hero p {{ color:#666; margin:0; }}
.sec-title {{ text-align:center; font-weight:600; font-size:1.8rem; margin:2rem 0 .2rem; }}
.sec-sub {{ text-align:center; color:#666; margin-bottom:1.2rem; }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.jobcard) {{ background:#F6EFFF; border:1px solid #E6D8F7; border-radius:10px; }}
.jobcard .t {{ font-weight:500; font-size:1.02rem; color:#2B2B2B; }}
.jobcard .m {{ font-size:.78rem; color:#777; margin:.15rem 0; }}
.jobcard .c {{ font-size:.85rem; color:#444; margin-top:.4rem; }}
.badge {{ display:inline-block; font-size:.66rem; font-weight:600; padding:1px 8px; border-radius:4px; margin-right:6px; letter-spacing:.3px; }}
.b-Full-time {{ background:#E6D8F7; color:{PURPLE}; }} .b-Part-time {{ background:#D8F5DF; color:#13813A; }}
.b-Internship {{ background:#FFF1D1; color:#9A6200; }} .b-Contract {{ background:#D9ECFF; color:#0B5CAD; }}
.b-Scholarship {{ background:#FFE0EC; color:#B0124F; }} .b-closed {{ background:#FDE0E0; color:#B00020; }}
.chip {{ display:inline-block; background:#fff; border:1px solid #E6D8F7; border-radius:20px; padding:4px 14px; margin:3px; font-size:.85rem; color:#444; }}
.stButton > button, .stFormSubmitButton > button, .stLinkButton > a {{ border-radius:6px; font-weight:500; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background:{PURPLE}; border-color:{PURPLE}; color:#fff; }}
.stButton > button[kind="secondary"] {{ border-color:{PURPLE}; color:{PURPLE}; background:#fff; }}
.footer {{ background:#F3EAFF; border-radius:14px; padding:1.6rem 2rem; margin-top:3rem; color:#555; font-size:.85rem; }}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ design system v2 (images + icons)
STATIC = Path(__file__).parent / "static"
HERO = ["clipboard", "tablet", "jobs", "office"]
P = "#6200B3"


def extra_css():
    slides = "".join(f".hero2 .s{i}{{background-image:url(/app/static/{n}.jpg);animation-delay:{i*6}s}}"
                     f".hero2 .d{i}{{animation-delay:{i*6}s}}" for i, n in enumerate(HERO))
    ib = [("nav_home", "house"), ("nav_find", "briefcase-business"), ("nav_post", "circle-plus"),
          ("nav_dash", "layout-dashboard"), ("nav_about", "info"), ("nav_reg", "user-plus"),
          ("nav_login", "log-in"), ("nav_logout", "log-out"), ("find_btn", "search"), ("search_btn", "search"),
          ("viewall_btn", "arrow-right"), ("goto_dash", "layout-dashboard"), ("firstjob", "circle-plus"),
          ("login_post", "log-in"), ("login_dash", "log-in"), ("dl_tpl", "download"), ("dl_export", "download"),
          ("import_btn", "upload")]
    icon_css = "".join(icons.mask_rule(f".st-key-{k} button", n) for k, n in ib)
    icon_css += icons.mask_rule('[class*="st-key-v_"] button', "eye")
    icon_css += icons.mask_rule('[class*="st-key-a_"] button', "send")
    icon_css += icons.mask_rule('[class*="st-key-close_"] button', "circle-x")
    icon_css += icons.mask_rule('[class*="st-key-reopen_"] button', "rotate-ccw")
    icon_css += icons.mask_rule('[class*="st-key-del_"] button', "trash-2")
    for i, n in enumerate(["clipboard-list", "inbox", "upload"], start=1):
        icon_css += icons.mask_rule(f'div[data-baseweb="tab-list"] button:nth-of-type({i})', n)
    return f"""<style>
.logo{{display:flex;align-items:center;gap:.5rem;padding-top:.15rem;letter-spacing:-.3px}}
.logo .tile{{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#8A2BE2,#4A0090);color:#fff;display:grid;place-items:center}}
.hero2{{position:relative;overflow:hidden;border-radius:20px;min-height:380px;background:#2A0058;margin:.6rem 0 0;color:#fff}}
.hero2 .slide{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;animation:nuruFade 24s infinite}}
.hero2::before{{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,rgba(38,0,80,.92) 0%,rgba(60,0,120,.62) 52%,rgba(60,0,120,.25) 100%)}}
.hero2 .hero-in{{position:relative;z-index:2;padding:3.2rem 3rem 5.2rem;max-width:720px}}
.hero2 h1{{font-size:2.6rem;font-weight:600;line-height:1.2;margin:.9rem 0 .7rem;color:#fff}}
.hero2 p{{color:rgba(255,255,255,.88);font-size:1.02rem;margin:0}}
.eyebrow{{display:inline-flex;align-items:center;gap:.45rem;background:rgba(255,255,255,.16);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.28);padding:.3rem .8rem;border-radius:99px;font-size:.78rem;font-weight:500}}
.hero2 .dots{{position:absolute;z-index:2;right:1.6rem;bottom:3.4rem;display:flex;gap:6px}}
.hero2 .dots i{{width:22px;height:4px;border-radius:4px;background:rgba(255,255,255,.35);animation:nuruDot 24s infinite}}
@keyframes nuruFade{{0%{{opacity:0;transform:scale(1)}}4%{{opacity:1}}25%{{opacity:1}}29%{{opacity:0;transform:scale(1.07)}}100%{{opacity:0}}}}
@keyframes nuruDot{{0%{{background:#fff;width:34px}}25%{{background:#fff;width:34px}}29%,100%{{background:rgba(255,255,255,.35);width:22px}}}}
{slides}
@media (prefers-reduced-motion:reduce){{.hero2 .slide,.hero2 .dots i{{animation:none}}.hero2 .s0{{opacity:1}}}}
@media (max-width:640px){{.hero2 .hero-in{{padding:2rem 1.3rem 4.6rem}}.hero2 h1{{font-size:1.8rem}}}}
.st-key-heroSearch{{margin:-3rem 1.6rem 1rem;background:#fff;border-radius:16px;padding:.9rem 1rem .4rem;box-shadow:0 16px 40px rgba(60,0,110,.20);position:relative;z-index:3}}
.banner{{position:relative;overflow:hidden;border-radius:16px;padding:2rem 2.2rem;margin:.2rem 0 1.4rem;color:#fff;background-size:cover;background-position:center 30%;background-color:#2A0058}}
.banner::before{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(38,0,80,.9),rgba(60,0,120,.45))}}
.banner>*{{position:relative}}
.banner h2{{color:#fff;margin:0;font-size:1.9rem;font-weight:600;padding:0}}
.banner p{{margin:.3rem 0 0;color:rgba(255,255,255,.88)}}
.authpanel{{position:relative;overflow:hidden;border-radius:18px;min-height:520px;padding:2rem;color:#fff;display:flex;flex-direction:column;justify-content:flex-end;background-size:cover;background-position:center}}
.authpanel::before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(38,0,80,.15) 0%,rgba(38,0,80,.92) 100%)}}
.authpanel>*{{position:relative}}
.authpanel h3{{color:#fff;font-size:1.5rem;font-weight:600;margin:0 0 .8rem}}
.authpanel .pt{{display:flex;align-items:center;gap:.6rem;margin:.35rem 0;font-size:.92rem}}
.stat{{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #E6D8F7;border-radius:14px;padding:1rem 1.2rem}}
.stat .ico{{width:46px;height:46px;border-radius:12px;background:#F3EAFF;color:{P};display:grid;place-items:center;flex:none}}
.stat b{{font-size:1.6rem;display:block;line-height:1.1;color:#2B2B2B}}
.stat .l{{color:#666;font-size:.8rem}}
.jobcard .m svg{{color:#8A6BB8;margin-right:2px}}
.jobcard .m .dot{{opacity:.4;margin:0 6px}}
.footer .fl{{display:flex;align-items:center;gap:.5rem;color:{P};font-weight:600;font-size:1rem;margin-bottom:.4rem}}
.st-key-q input,.st-key-loc input{{padding-left:2.6rem !important;background-repeat:no-repeat;background-position:.85rem center;background-size:1.1rem}}
.st-key-q input{{background-image:url({icons.data_uri("search", P)})}}
.st-key-loc input{{background-image:url({icons.data_uri("map-pin", P)})}}
{icon_css}
</style>"""


st.markdown(extra_css(), unsafe_allow_html=True)

# ------------------------------------------------------------------ state / auth helpers
ss = st.session_state
ss.setdefault("page", "Home")
ss.setdefault("user", None)
ss.setdefault("limit", 8)


def go(page):
    ss.page = page


def admin_emails():
    raw = os.environ.get("NURU_ADMIN_EMAILS", "")
    try:
        raw = raw or st.secrets.get("ADMIN_EMAILS", "")
    except Exception:
        pass
    return {e.strip().lower() for e in str(raw).split(",") if e.strip()}


def is_admin():
    return bool(ss.user and ss.user["role"] == "admin")


def login_user(u):
    if u["email"] in admin_emails() and u["role"] != "admin":
        db.set_role(u["email"], "admin")
        u["role"] = "admin"
    ss.user = {k: u[k] for k in ("email", "name", "role")}


def banner(title, subtitle, img):
    st.markdown(f'<div class="banner" style="background-image:url(/app/static/{img}.jpg)"><h2>{esc(title)}</h2>'
                f'<p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x or ""))


def fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return ""


def is_closed(row):
    if row["status"] == "closed":
        return True
    d = row["deadline"]
    return bool(d) and not pd.isna(d) and d < date.today().isoformat()


def salary_text(row):
    lo, hi, cur = row["salary_min"], row["salary_max"], row["currency"] or "UGX"
    lo = None if pd.isna(lo) else lo
    hi = None if pd.isna(hi) else hi
    if lo and hi:
        return f"{cur} {lo:,.0f} - {hi:,.0f}"
    if lo or hi:
        return f"{cur} {(lo or hi):,.0f}"
    return ""


# ------------------------------------------------------------------ shared UI
def navbar():
    items = [("Home", "nav_home"), ("Find Jobs", "nav_find"), ("Post a Job", "nav_post"),
             ("Dashboard", "nav_dash"), ("About", "nav_about")]
    cols = st.columns([1.5] + [1.1] * len(items) + [1.1, 1.1])
    cols[0].markdown(f'<div class="logo"><span class="tile">{ic("sparkles", 18, "#fff")}</span>Nuru</div>',
                     unsafe_allow_html=True)
    for i, (p, k) in enumerate(items, start=1):
        cols[i].button(p, key=k, on_click=go, args=(p,), use_container_width=True,
                       type="primary" if ss.page == p else "secondary")
    if ss.user:
        cols[-2].caption(f"Hi, {ss.user['name'].split()[0]}")
        if cols[-1].button("Logout", key="nav_logout", use_container_width=True):
            ss.user = None
            ss.page = "Home"
            st.rerun()
    else:
        cols[-2].button("Register", key="nav_reg", on_click=go, args=("Register",), use_container_width=True)
        cols[-1].button("Login", key="nav_login", on_click=go, args=("Login",), use_container_width=True, type="primary")
    st.divider()


def footer():
    st.markdown(f"""<div class="footer"><div class="fl">{ic("sparkles", 18, P)} Nuru</div>
    Jobs, internships and scholarships for Ugandans.<br>
    {ic("map-pin", 13)} Kampala, Uganda &nbsp;|&nbsp; Always confirm deadlines and requirements on the official listing before applying.<br>
    © 2026 Nuru. All rights reserved.</div>""", unsafe_allow_html=True)


def card_html(r):
    closed = is_closed(r)
    badges = f'<span class="badge b-{esc(r["job_type"])}">{esc(str(r["job_type"]).upper())}</span>'
    if closed:
        badges += '<span class="badge b-closed">CLOSED</span>'
    sal = salary_text(r)
    if sal:
        meta = f"Salary: {esc(sal)}"
    elif r["deadline"]:
        meta = f'{ic("calendar", 13)} Closes {fmt_date(r["deadline"])}'
    else:
        meta = ""
    org = esc(r["company"]) or ("Scholarship" if r["kind"] == "Scholarship" else "Employer")
    app = f'<span class="dot">•</span>{ic("users", 13)} {int(r["applicants"])} applicant(s)' if r["applicants"] else ""
    return (f'<div class="jobcard"><div class="t">{esc(r["title"])}</div>'
            f'<div class="m">{badges}{meta}</div>'
            f'<div class="c"><b>{org}</b></div>'
            f'<div class="m">{ic("map-pin", 13)} {esc(r["location"])}<span class="dot">•</span>'
            f'{ic("tag", 13)} {esc(r["category"])}{app}</div></div>')


@st.dialog("Opportunity details", width="large")
def detail_dialog(lid):
    r = db.get_listing(lid)
    if not r:
        st.error("Listing not found.")
        return
    row = pd.Series(r)
    row["applicants"] = 0
    st.markdown(f"### {r['title']}")
    st.markdown(card_html(row), unsafe_allow_html=True)
    st.write(r["description"] or "No description provided.")
    if r["deadline"]:
        st.caption(f"Deadline: {fmt_date(r['deadline'])}")
    if is_closed(row):
        st.warning("This listing is closed or past its deadline. Check the official page in case it was extended.")
    if r["url"]:
        st.link_button("Open official listing / apply", r["url"], type="primary")
    if r["apply_email"]:
        st.markdown(f"Or email your CV to **{r['apply_email']}**")
    if r["source"] == "form" and r["status"] == "active":
        st.markdown("#### Apply on Nuru")
        u = ss.user or {}
        with st.form(f"apply_{lid}", clear_on_submit=True):
            name = st.text_input("Full name", value=u.get("name", ""))
            email = st.text_input("Email", value=u.get("email", ""))
            phone = st.text_input("Phone")
            msg = st.text_area("Cover note")
            if st.form_submit_button("Submit application", type="primary"):
                if not (name.strip() and "@" in email):
                    st.error("Name and a valid email are required.")
                else:
                    db.add_application(lid, name, email, phone, msg)
                    st.success("Application sent. The employer will see it on their dashboard.")


def listing_grid(df, ctx, ncols=2):
    for i in range(0, len(df), ncols):
        cols = st.columns(ncols)
        for col, (_, r) in zip(cols, df.iloc[i:i + ncols].iterrows()):
            with col, st.container(border=True):
                st.markdown(card_html(r), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("View details", key=f"v_{ctx}_{r['id']}", use_container_width=True):
                    detail_dialog(int(r["id"]))
                if b2.button("Apply now", key=f"a_{ctx}_{r['id']}", use_container_width=True, type="primary"):
                    detail_dialog(int(r["id"]))



SLIDES = [
    ("clipboard", "Apply with confidence", "Review requirements, deadlines and how to apply before you submit."),
    ("tablet", "Careers in every sector", "Finance, health, ICT, engineering, development and more."),
    ("jobs", "Employers, hire faster", "Post a vacancy in minutes and manage applicants from one dashboard."),
    ("office", "Never miss a deadline", "Track closing dates across jobs, internships and scholarships."),
]


@st.cache_data(show_spinner=False)
def carousel_html():
    def b64(n):
        return base64.b64encode((STATIC / f"{n}_sm.jpg").read_bytes()).decode()
    slides = "".join(
        f'<figure class="sl{" on" if i == 0 else ""}" style="background-image:url(data:image/jpeg;base64,{b64(n)})" '
        f'role="group" aria-roledescription="slide" aria-label="{i+1} of {len(SLIDES)}">'
        f'<figcaption><h3>{t}</h3><p>{d}</p></figcaption></figure>' for i, (n, t, d) in enumerate(SLIDES))
    dots = "".join(f'<button class="dot{" on" if i == 0 else ""}" aria-label="Go to slide {i+1}"></button>'
                   for i in range(len(SLIDES)))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');
*{{box-sizing:border-box}} body{{margin:0;font-family:'Poppins',sans-serif}}
.car{{position:relative;height:400px;border-radius:18px;overflow:hidden;background:#2A0058;outline-offset:3px}}
.sl{{position:absolute;inset:0;margin:0;background-size:cover;background-position:center;opacity:0;transition:opacity .8s ease;display:flex;align-items:flex-end}}
.sl.on{{opacity:1}}
.sl::before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(38,0,80,0) 35%,rgba(38,0,80,.9) 100%)}}
figcaption{{position:relative;color:#fff;padding:0 2.2rem 3.2rem;max-width:620px}}
figcaption h3{{margin:0 0 .3rem;font-size:1.6rem;font-weight:600}} figcaption p{{margin:0;opacity:.9;font-size:.95rem}}
.nav{{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;border-radius:50%;border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.16);backdrop-filter:blur(6px);color:#fff;display:grid;place-items:center;cursor:pointer;transition:background .2s}}
.nav:hover,.nav:focus-visible{{background:rgba(255,255,255,.34)}} .prev{{left:14px}} .next{{right:14px}}
.dots{{position:absolute;left:2.2rem;bottom:1.3rem;display:flex;gap:8px}}
.dot{{width:22px;height:4px;border:0;border-radius:4px;background:rgba(255,255,255,.4);cursor:pointer;padding:0;transition:all .3s}}
.dot.on{{width:38px;background:#fff}}
@media (prefers-reduced-motion:reduce){{.sl{{transition:none}}}}
@media (max-width:560px){{.car{{height:340px}}figcaption{{padding:0 1.2rem 3rem}}.dots{{left:1.2rem}}}}
</style></head><body>
<div class="car" tabindex="0" role="region" aria-roledescription="carousel" aria-label="Why Nuru">
{slides}
<button class="nav prev" aria-label="Previous slide">{ic("chevron-left", 22, "#fff")}</button>
<button class="nav next" aria-label="Next slide">{ic("chevron-right", 22, "#fff")}</button>
<div class="dots">{dots}</div></div>
<script>
const car=document.querySelector('.car'),sl=[...car.querySelectorAll('.sl')],dt=[...car.querySelectorAll('.dot')];
let i=0,t=null;const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function show(n){{i=(n+sl.length)%sl.length;sl.forEach((e,k)=>e.classList.toggle('on',k===i));
 dt.forEach((e,k)=>{{e.classList.toggle('on',k===i);k===i?e.setAttribute('aria-current','true'):e.removeAttribute('aria-current')}})}}
function play(){{if(!reduce&&!t)t=setInterval(()=>show(i+1),5500)}} function stop(){{clearInterval(t);t=null}}
car.querySelector('.prev').onclick=()=>show(i-1);car.querySelector('.next').onclick=()=>show(i+1);
dt.forEach((e,k)=>e.onclick=()=>show(k));
car.addEventListener('mouseenter',stop);car.addEventListener('mouseleave',play);
car.addEventListener('focusin',stop);car.addEventListener('focusout',play);
car.addEventListener('keydown',e=>{{if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1)}});
let x0=null;car.addEventListener('touchstart',e=>x0=e.touches[0].clientX,{{passive:true}});
car.addEventListener('touchend',e=>{{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>40)show(i+(d<0?1:-1));x0=null}});
play();
</script></body></html>"""


def render_carousel():
    page = carousel_html()
    if hasattr(st, "iframe"):          # Streamlit >= 1.5x
        st.iframe(page, height=410)
    else:                              # older Streamlit
        components.html(page, height=410)


def search_to_jobs():
    ss.page = "Find Jobs"
    ss.limit = 8


# ------------------------------------------------------------------ pages
def page_home():
    df = db.listings_df()
    jobs = df[df.kind == "Job"]
    n = len(HERO)
    slides = "".join(f'<div class="slide s{i}"></div>' for i in range(n))
    dots = "".join(f'<i class="d{i}"></i>' for i in range(n))
    st.markdown(f"""<div class="hero2">{slides}<div class="hero-in">
    <span class="eyebrow">{ic("sparkles", 14)} Jobs · Internships · Scholarships</span>
    <h1>Find an opportunity that fits<br>your interests and skills</h1>
    <p>Jobs, internships and scholarships in Uganda and beyond, all in one place.</p></div>
    <div class="dots">{dots}</div></div>""", unsafe_allow_html=True)
    with st.container(key="heroSearch"):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.text_input("Job title, keyword...", key="q", label_visibility="collapsed", placeholder="Job title, keyword...")
        c2.text_input("Location", key="loc", label_visibility="collapsed", placeholder="Location")
        c3.button("Find Job", key="find_btn", type="primary", use_container_width=True, on_click=search_to_jobs)
    st.caption("Suggestion: Accountant, Nurse, Engineer, Scholarship, Internship")

    st.markdown('<div class="sec-title">Featured Jobs</div><div class="sec-sub">Choose from top employers and apply.</div>',
                unsafe_allow_html=True)
    live = jobs[~jobs.apply(is_closed, axis=1)] if len(jobs) else jobs
    feat = (live if len(live) >= 3 else jobs).head(3)
    if len(feat):
        listing_grid(feat, "home", ncols=3)
    st.button("View all", key="viewall_btn", on_click=search_to_jobs)

    st.markdown('<div class="sec-title">Built for every step of your career</div>'
                '<div class="sec-sub">From first application to final offer.</div>', unsafe_allow_html=True)
    render_carousel()

    top = jobs[jobs.company != ""].company.value_counts().head(10).index.tolist()
    if top:
        st.markdown('<div class="sec-sub" style="margin-top:2rem">Top organisations hiring now</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center">' + "".join(f'<span class="chip">{esc(t)}</span>' for t in top) + "</div>",
                    unsafe_allow_html=True)
    st.write("")
    stats = [("briefcase", len(jobs), "Jobs & internships"), ("graduation-cap", int((df.kind == "Scholarship").sum()), "Scholarships"),
             ("building-2", int(df.company.replace("", pd.NA).nunique()), "Organisations")]
    for col, (icn, val, lab) in zip(st.columns(3), stats):
        col.markdown(f'<div class="stat"><div class="ico">{ic(icn, 22, PURPLE)}</div><div><b>{val}</b>'
                     f'<span class="l">{lab}</span></div></div>', unsafe_allow_html=True)
    footer()


def page_find():
    df = db.listings_df()
    banner("Job Search", "Search for your desired job matching your skills", "jobs")
    c1, c2, c3 = st.columns([3, 2, 1])
    q = c1.text_input("Job title / keyword", key="q", placeholder="Job title, keyword...", label_visibility="collapsed")
    loc = c2.text_input("Location", key="loc", placeholder="Location", label_visibility="collapsed")
    c3.button("Search", key="search_btn", type="primary", use_container_width=True)

    left, right = st.columns([1, 3])
    with left:
        h1, h2 = st.columns([1, 1])
        h1.markdown("**Filter**")
        if h2.button("Clear all"):
            for k in ("q", "loc", "f_kind", "f_type", "f_mode", "f_cat", "f_hide"):
                ss.pop(k, None)
            st.rerun()
        kind = st.radio("Show", ["All", "Job", "Scholarship"], key="f_kind", horizontal=True,
                        format_func=lambda x: {"All": "All", "Job": "Jobs", "Scholarship": "Scholarships"}[x])
        base = df if kind == "All" else df[df.kind == kind]
        jt = st.multiselect("Job type", sorted(base.job_type.unique()), key="f_type")
        wm = st.multiselect("Work mode", [m for m in importer.WORK_MODES if m in set(base.work_mode)], key="f_mode")
        cats = base.category.value_counts()
        cat = st.multiselect("Category", list(cats.index), key="f_cat", format_func=lambda c: f"{c} ({cats[c]})")
        hide = st.checkbox("Hide closed / expired", key="f_hide")
        with st.expander("Salary range (UGX)"):
            smin = st.number_input("Min", min_value=0, step=100000, value=0)
            smax = st.number_input("Max", min_value=0, step=100000, value=0)

    f = base
    if q:
        blob = (f.title + " " + f.company + " " + f.description + " " + f.category).str.lower()
        for w in q.lower().split():
            f = f[blob.loc[f.index].str.contains(w, regex=False)]
    if loc:
        f = f[f.location.str.lower().str.contains(loc.lower(), regex=False)]
    if jt:
        f = f[f.job_type.isin(jt)]
    if wm:
        f = f[f.work_mode.isin(wm)]
    if cat:
        f = f[f.category.isin(cat)]
    if hide and len(f):
        f = f[~f.apply(is_closed, axis=1)]
    if smin:
        f = f[f.salary_max.fillna(f.salary_min).fillna(0) >= smin]
    if smax:
        f = f[f.salary_min.fillna(f.salary_max).fillna(0).le(smax) | f.salary_min.isna() & f.salary_max.isna()]

    with right:
        t1, t2 = st.columns([3, 1])
        t1.markdown(f"### All Listings ({len(f)})")
        sort = t2.selectbox("Sort", ["Latest", "Deadline soon", "Most applied"], label_visibility="collapsed")
        if sort == "Deadline soon":
            f = f.assign(_d=f.deadline.fillna("9999")).sort_values("_d")
        elif sort == "Most applied":
            f = f.sort_values("applicants", ascending=False)
        if f.empty:
            st.info("No listings match your filters.")
        else:
            listing_grid(f.head(ss.limit), "find")
            if len(f) > ss.limit:
                st.button("View more", on_click=lambda: ss.update(limit=ss.limit + 8))
    footer()


def page_post():
    banner("Post a job", "Find the best talent for your company", "tablet")
    if not ss.user:
        st.info("Please log in or register as an employer to post a job.")
        st.button("Login", key="login_post", on_click=go, args=("Login",), type="primary")
        return
    existing = db.listings_df()
    cats = sorted(set(existing.category) | set(CATEGORY_FALLBACK))
    with st.form("post_job", clear_on_submit=True):
        title = st.text_input("Job title*", placeholder="e.g. Senior Accountant")
        company = st.text_input("Company / organisation*", value=ss.user["name"])
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category*", cats)
        job_type = c2.selectbox("Job type", ["Full-time", "Part-time", "Internship", "Contract"])
        c3, c4 = st.columns(2)
        work_mode = c3.selectbox("Work mode", importer.WORK_MODES)
        location = c4.text_input("Location*", value="Kampala")
        s1, s2, s3 = st.columns(3)
        currency = s1.selectbox("Currency", ["UGX", "USD", "KES", "EUR"])
        smin = s2.number_input("Min salary", min_value=0, step=100000)
        smax = s3.number_input("Max salary", min_value=0, step=100000)
        d1, d2 = st.columns(2)
        deadline = d1.date_input("Application deadline", value=None, min_value=date.today())
        apply_email = d2.text_input("Application email or URL (optional)")
        desc = st.text_area("Job description*", height=180, placeholder="Responsibilities, requirements, how to apply...")
        ok = st.form_submit_button("Post Job", type="primary")
    if ok:
        if not (title.strip() and company.strip() and location.strip() and desc.strip()):
            st.error("Title, company, location and description are required.")
        else:
            is_url = apply_email.strip().lower().startswith("http")
            db.post_job(dict(kind="Job", title=title.strip(), company=company.strip(), category=category,
                             job_type=job_type, work_mode=work_mode, location=location.strip(),
                             salary_min=smin or None, salary_max=smax or None, currency=currency,
                             deadline=deadline.isoformat() if deadline else None, description=desc.strip(),
                             url=apply_email.strip() if is_url else "",
                             apply_email="" if is_url else apply_email.strip()), ss.user["email"])
            st.success("Job posted. It is now live on Find Jobs and listed on your dashboard.")
            st.button("Go to dashboard", key="goto_dash", on_click=go, args=("Dashboard",), type="primary")


def bulk_upload_ui(owner):
    st.markdown("#### Bulk upload from Excel / CSV")
    st.caption("Use the same layout as hub_repo.xlsx: **path, title, url, details**. "
               "Duplicates (same URL) are skipped automatically.")
    tpl = pd.DataFrame([{"path": "Jobs/Banks & Finance", "title": "Example Bank - Credit Officer",
                         "url": "https://example.com/job/1",
                         "details": "Kampala. Closes 30 Dec 2026. Degree in Finance, 2 yrs experience. Email CV to hr@example.com"}])
    buf = io.BytesIO()
    tpl.to_excel(buf, index=False)
    st.download_button("Download template", buf.getvalue(), "nuru_template.xlsx", key="dl_tpl")
    up = st.file_uploader("Upload .xlsx or .csv", type=["xlsx", "csv"])
    if up:
        try:
            items = importer.parse_dataframe(importer.read_file(up))
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return
        prev = pd.DataFrame(items)[["kind", "title", "company", "category", "location", "deadline"]]
        st.write(f"{len(items)} rows parsed. Preview:")
        st.dataframe(prev, use_container_width=True, hide_index=True)
        if st.button(f"Import {len(items)} listings", key="import_btn", type="primary"):
            added, skipped = db.bulk_add(items, source="excel", owner=owner)
            st.success(f"Added {added}. Skipped {skipped} duplicate(s).")
            st.rerun()


def page_dashboard():
    banner("Dashboard", "Manage your listings, applications and uploads", "office")
    if not ss.user:
        st.info("Log in to see your dashboard.")
        st.button("Login", key="login_dash", on_click=go, args=("Login",), type="primary")
        return
    admin = is_admin()
    owner = ss.user["email"]
    scope_all = admin and st.toggle("Admin view: show every listing", value=True)
    mine = db.listings_df(None if scope_all else owner)
    apps = db.applications_df(None if scope_all else owner)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total listings", len(mine))
    m2.metric("Active", int((~mine.apply(is_closed, axis=1)).sum()) if len(mine) else 0)
    m3.metric("Applications received", len(apps))

    t1, t2, t3 = st.tabs(["Posted jobs", "Applications", "Bulk upload & export"])
    with t1:
        if mine.empty:
            st.info("Nothing posted yet.")
            st.button("Post your first job", key="firstjob", on_click=go, args=("Post a Job",), type="primary")
        else:
            q = st.text_input("Filter this list", placeholder="Search title, company, category...")
            lst = mine
            if q:
                blob = (mine.title + " " + mine.company + " " + mine.category).str.lower()
                lst = mine[blob.str.contains(q.lower(), regex=False)]
            page_size = 15
            pages = max(1, -(-len(lst) // page_size))
            pg = st.number_input("Page", 1, pages, 1) if pages > 1 else 1
            for _, r in lst.iloc[(pg - 1) * page_size: pg * page_size].iterrows():
                with st.container(border=True):
                    a, b, c, d = st.columns([5, 1.4, 1.2, 1.2])
                    a.markdown(card_html(r), unsafe_allow_html=True)
                    a.caption(f"Posted {r['created_at'][:10]} · {r['source']}")
                    b.metric("Applicants", int(r["applicants"]))
                    if r["status"] == "active":
                        c.button("Close", key=f"close_{r['id']}", on_click=db.set_status, args=(int(r["id"]), "closed"),
                                 use_container_width=True)
                    else:
                        c.button("Reopen", key=f"reopen_{r['id']}", on_click=db.set_status, args=(int(r["id"]), "active"),
                                 use_container_width=True)
                    d.button("Delete", key=f"del_{r['id']}", on_click=db.delete_listing, args=(int(r["id"]),),
                             use_container_width=True)
    with t2:
        if apps.empty:
            st.info("No applications yet.")
        else:
            st.dataframe(apps, use_container_width=True, hide_index=True)
    with t3:
        bulk_upload_ui(owner)
        st.divider()
        st.markdown("#### Export (backup)")
        out = mine.drop(columns=["dedupe_key"], errors="ignore")
        buf = io.BytesIO()
        out.to_excel(buf, index=False)
        st.download_button("Download listings (.xlsx)", buf.getvalue(), "nuru_listings.xlsx", key="dl_export")


def auth_form(register):
    left, mid = st.columns([1.05, 1], gap="large")
    img = "tablet" if register else "clipboard"
    pts = (["Post jobs and manage applicants", "Bulk-upload vacancies from Excel", "Track everything on one dashboard"]
           if register else ["Pick up where you left off", "Track your postings and applications", "Secure sign-in"])
    ptic = ["briefcase-business", "file-spreadsheet", "layout-dashboard"] if register else ["clock", "list-checks", "shield-check"]
    with left:
        st.markdown(f'<div class="authpanel" style="background-image:url(/app/static/{img}.jpg)">'
                    f'<h3>{"Join Nuru today" if register else "Welcome back"}</h3>'
                    + "".join(f'<div class="pt">{ic(i, 18)} {esc(p)}</div>' for i, p in zip(ptic, pts))
                    + "</div>", unsafe_allow_html=True)
    with mid:
        st.markdown(f"## {'Create your account' if register else 'Login to your account'}")
        with st.form("auth"):
            if register:
                name = st.text_input("Full name*")
            email = st.text_input("Email ID*")
            if register:
                phone = st.text_input("Mobile number*", placeholder="+256 ...")
                role = st.radio("I am a", ["candidate", "employer"], horizontal=True,
                                format_func=lambda x: x.title())
            pw = st.text_input("Password*" + (" (min 6 characters)" if register else ""), type="password")
            ok = st.form_submit_button("Register now" if register else "Login", type="primary", use_container_width=True)
        if ok:
            if register:
                if not (name.strip() and "@" in email and phone.strip() and len(pw) >= 6):
                    st.error("Fill every field. Password needs at least 6 characters.")
                else:
                    role = "admin" if email.strip().lower() in admin_emails() else role
                    if db.create_user(email, name, phone, pw, role):
                        login_user(db.verify_user(email, pw))
                        ss.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("That email is already registered.")
            else:
                u = db.verify_user(email, pw)
                if u:
                    login_user(u)
                    ss.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Wrong email or password.")
        if register:
            st.button("Already have an account? Login", on_click=go, args=("Login",))
        else:
            st.button("Don't have an account? Register", on_click=go, args=("Register",))


def page_about():
    banner("About Nuru", "Light for your next step", "jobs")
    st.write("Nuru (Luganda/Swahili for *light*) helps Ugandans find jobs, internships and scholarships in one place, "
             "and lets employers post vacancies and manage applications.")
    st.markdown(f"{ic('map-pin', 15)} &nbsp;**Contact:** Kampala, Uganda", unsafe_allow_html=True)
    footer()


navbar()
{"Home": page_home, "Find Jobs": page_find, "Post a Job": page_post, "Dashboard": page_dashboard,
 "About": page_about, "Login": lambda: auth_form(False), "Register": lambda: auth_form(True)}[ss.page]()
