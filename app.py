import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Chargers Baseball",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Navy/Gold theme ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background-color: #f5f6fa; }
  .hero {
    background: linear-gradient(135deg, #1A3A6C 0%, #2A5298 100%);
    border-radius: 12px; padding: 1.8rem 2rem;
    text-align: center; margin-bottom: 1.2rem;
  }
  .hero h1 { color: #CFB53B; margin: 0; font-size: 2rem; letter-spacing: 1px; }
  .hero p  { color: rgba(255,255,255,.88); margin:.4rem 0 0; font-size:.95rem; }
  .badge {
    background: #1A3A6C; color: #CFB53B; border-radius: 5px;
    padding: .3rem .9rem; font-weight: 700; font-size: .85rem;
    display: inline-block; margin: .6rem 0 .3rem; letter-spacing: .5px;
  }
  div[data-testid="stDataFrame"] { border-radius: 6px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚾ Benjamin Franklin Chargers Baseball</h1>
  <p>All-time statistics &nbsp;·&nbsp; 2016-17 through 2025-26
     &nbsp;·&nbsp; Queen Creek, AZ &nbsp;·&nbsp; 3A Conference</p>
</div>
""", unsafe_allow_html=True)

# ── Load data from Excel ───────────────────────────────────────────────────────
EXCEL = "Franklin_Baseball_Stats.xlsx"

@st.cache_data
def load_sheets():
    xl = pd.ExcelFile(EXCEL)
    # All sheets were written with 2 title rows then 1 header row → header=2
    data = {}
    skip = {"Season Records"}          # custom layout; re-computed below
    for name in xl.sheet_names:
        if name not in skip:
            data[name] = pd.read_excel(xl, name, header=2)
    return data

sheets = load_sheets()

df_rec    = sheets["Team Records"]
df_sb     = sheets["Season Batting"]   # season batting
df_sp     = sheets["Season Pitching"]  # season pitching
df_cb     = sheets["Career Batting"]
df_cp     = sheets["Career Pitching"]
df_lb_bat = sheets["Batting Leaderboard"]
df_lb_pit = sheets["Pitching Leaderboard"]

# ── Helper: innings-pitched string → decimal ──────────────────────────────────
def ip_dec(ip):
    try:
        v = float(str(ip)); w = int(v); f = round((v - w) * 10)
        return w + f / 3.0
    except:
        return 0.0

# ── Build season record book from the season sheets ───────────────────────────
@st.cache_data
def make_season_records(sb, sp, pa_factor=2.1, min_ip=13.0):
    team_games = sb.groupby("Season")["GP"].max()

    def bat_best(col):
        s = sb.dropna(subset=[col])
        if s.empty: return None, None, None, None
        r = s.loc[s[col].idxmax()]
        return r[col], r["Player"], r["Class"], r["Season"]

    def bat_best_qual(col):
        mask = sb.apply(
            lambda r: (r.get("PA", 0) or 0) >=
                      math.ceil(team_games.get(r["Season"], 0) * pa_factor)
                      and (r.get("AB", 0) or 0) > 0,
            axis=1)
        s = sb[mask].dropna(subset=[col])
        if s.empty: return None, None, None, None
        r = s.loc[s[col].idxmax()]
        return r[col], r["Player"], r["Class"], r["Season"]

    def pit_best(col, df, lower=False):
        s = df.dropna(subset=[col])
        if s.empty: return None, None, None, None
        r = s.loc[(s[col].idxmin() if lower else s[col].idxmax())]
        return r[col], r["Player"], r["Class"], r["Season"]

    spq = sp.copy()
    spq["_ip"] = spq["IP"].apply(ip_dec)
    spq = spq[spq["_ip"] >= min_ip].copy()
    spq["WHIP"] = (spq["H"] + spq["BB"]) / spq["_ip"]

    recs = []
    for lbl, col in [("Home Runs","HR"),("Triples","3B"),("Doubles","2B"),
                     ("RBIs","RBI"),("Runs Scored","R"),("Hits","H"),
                     ("Stolen Bases","SB")]:
        v, p, c, s = bat_best(col)
        recs.append(("BATTING", lbl, int(v) if v is not None else None, p, c, s))

    for lbl, col in [("Batting Average","AVG"),("OPS","OPS")]:
        v, p, c, s = bat_best_qual(col)
        recs.append(("BATTING", f"{lbl}  (min {pa_factor} PA/game)",
                     round(float(v),3) if v is not None else None, p, c, s))

    for lbl, col in [("Strikeouts","K"),("Wins","W")]:
        v, p, c, s = pit_best(col, sp)
        recs.append(("PITCHING", lbl, int(v) if v is not None else None, p, c, s))

    v, p, c, s = pit_best("ERA",  spq, lower=True)
    recs.append(("PITCHING", f"ERA  (min {int(min_ip)} IP)",
                 round(float(v),3) if v is not None else None, p, c, s))
    v, p, c, s = pit_best("WHIP", spq, lower=True)
    recs.append(("PITCHING", f"WHIP  (min {int(min_ip)} IP)",
                 round(float(v),3) if v is not None else None, p, c, s))

    return recs

season_recs = make_season_records(df_sb, df_sp)

# ── Column config helpers ─────────────────────────────────────────────────────
def nc(lbl, fmt, **kw):
    return st.column_config.NumberColumn(lbl, format=fmt, **kw)

BAT_CC = {"AVG": nc("AVG","%.3f"), "OBP": nc("OBP","%.3f"),
          "SLG": nc("SLG","%.3f"), "OPS": nc("OPS","%.3f")}
PIT_CC = {"ERA": nc("ERA","%.2f"), "WHIP": nc("WHIP","%.3f"),
          "K/9": nc("K/9","%.1f"),  "BB/9": nc("BB/9","%.1f"),
          "W%":  nc("W%","%.3f")}

def show_df(df, cc=None, **kw):
    st.dataframe(df.reset_index(drop=True), use_container_width=True,
                 hide_index=True, column_config=cc, **kw)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆  Career Leaderboards",
    "📋  Season Records",
    "🔍  Player Lookup",
    "📅  Team Records",
])

# ── Tab 1: Career Leaderboards ────────────────────────────────────────────────
with tab1:
    b_tab, p_tab = st.tabs(["🏏 Batting", "⚾ Pitching"])

    with b_tab:
        st.caption("Minimum 30 AB to qualify for rate stats · click any column header to sort")
        lb = df_lb_bat.copy()
        # Drop Rank column if present (index already hidden)
        if "Rank" in lb.columns:
            lb = lb.drop(columns=["Rank"])
        show_df(lb, BAT_CC)

    with p_tab:
        st.caption("Minimum 15 IP to qualify · click any column header to sort")
        lb = df_lb_pit.copy()
        if "Rank" in lb.columns:
            lb = lb.drop(columns=["Rank"])
        show_df(lb, PIT_CC)

# ── Tab 2: Season Records ─────────────────────────────────────────────────────
with tab2:
    st.caption(
        "Best single-season performances · "
        "Batting rate stats: min 2.1 PA/game · "
        "Pitching rate stats: min 13 IP · "
        "SB not recorded in 2016-17 or 2017-18"
    )
    bat_r = [(c,v,p,cl,s) for sec,c,v,p,cl,s in season_recs if sec == "BATTING"]
    pit_r = [(c,v,p,cl,s) for sec,c,v,p,cl,s in season_recs if sec == "PITCHING"]
    RCOLS = ["Category","Record","Player","Class","Season"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="badge">BATTING</div>', unsafe_allow_html=True)
        show_df(pd.DataFrame(bat_r, columns=RCOLS),
                {"Record": st.column_config.NumberColumn("Record", format="%.3f")})
    with c2:
        st.markdown('<div class="badge">PITCHING</div>', unsafe_allow_html=True)
        show_df(pd.DataFrame(pit_r, columns=RCOLS),
                {"Record": st.column_config.NumberColumn("Record", format="%.3f")})

# ── Tab 3: Player Lookup ──────────────────────────────────────────────────────
with tab3:
    # Build unique player list from career sheets (covers both batters & pitchers)
    cb_ids = df_cb[["Player","GradYr"]].copy()
    cp_ids = df_cp[["Player","GradYr"]].copy()
    all_pl = (pd.concat([cb_ids, cp_ids])
                .drop_duplicates()
                .sort_values("Player")
                .reset_index(drop=True))

    def pl_label(row):
        try:
            gy = int(row["GradYr"])
            return f"{row['Player']}  (Grad '{str(gy)[-2:]})"
        except:
            return str(row["Player"])

    option_map = {pl_label(r): (r["Player"], r["GradYr"])
                  for _, r in all_pl.iterrows()}

    sel = st.selectbox(
        "Search for a player:",
        list(option_map.keys()),
        index=None,
        placeholder="Start typing a name…",
    )

    if sel:
        name, gy = option_map[sel]

        # Match by name; use GradYr when available to disambiguate
        def match(df, player_col="Player", gy_col="GradYr"):
            name_m = df[player_col] == name
            if pd.isna(gy):
                return df[name_m]
            try:
                return df[name_m & (df[gy_col].fillna(-1).astype(int) == int(gy))]
            except:
                return df[name_m]

        sb_rows = match(df_sb)
        sp_rows = match(df_sp)
        cb_rows = match(df_cb)
        cp_rows = match(df_cp)

        gy_str = f"  ·  Grad '{str(int(gy))[-2:]}" if pd.notna(gy) else ""
        st.markdown(f"### {name}{gy_str}")
        st.markdown("---")

        # ── Batting ───────────────────────────────────────────────────────────
        if not sb_rows.empty:
            BAT_COLS = ["Season","Class","GP","AVG","PA","AB","R","H","RBI",
                        "2B","3B","HR","BB","K","HBP","OBP","SLG","OPS","SB"]
            BAT_COLS = [c for c in BAT_COLS if c in sb_rows.columns]
            st.markdown("**Season Batting**")
            show_df(sb_rows[BAT_COLS], BAT_CC)

            if not cb_rows.empty:
                CAR_BAT = ["GP","AVG","PA","AB","R","H","RBI","2B","3B","HR",
                           "BB","K","HBP","SB","OBP","SLG","OPS"]
                CAR_BAT = [c for c in CAR_BAT if c in cb_rows.columns]
                st.markdown("**Career Batting Totals**")
                show_df(cb_rows[CAR_BAT], BAT_CC)

        # ── Pitching ──────────────────────────────────────────────────────────
        if not sp_rows.empty:
            PIT_COLS = ["Season","Class","ERA","W","L","APP","GS","SV",
                        "IP","H","R","ER","BB","K","Pitches"]
            PIT_COLS = [c for c in PIT_COLS if c in sp_rows.columns]
            st.markdown("**Season Pitching**")
            show_df(sp_rows[PIT_COLS], PIT_CC)

            if not cp_rows.empty:
                CAR_PIT = ["ERA","W","L","W%","APP","GS","SV","IP",
                           "H","R","ER","BB","K","K/9","BB/9","WHIP"]
                CAR_PIT = [c for c in CAR_PIT if c in cp_rows.columns]
                st.markdown("**Career Pitching Totals**")
                show_df(cp_rows[CAR_PIT], PIT_CC)

        if sb_rows.empty and sp_rows.empty:
            st.info("No season data found for this player.")

# ── Tab 4: Team Records ───────────────────────────────────────────────────────
with tab4:
    st.caption("All-time season records for the Chargers varsity program")
    show_df(df_rec)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data: 2016-17 through 2025-26  ·  Built with Streamlit  ·  "
           "Benjamin Franklin High School, Queen Creek AZ")
