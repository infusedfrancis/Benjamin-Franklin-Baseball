import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Franklin Chargers Athletics",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global theme ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background-color: #f5f6fa; }

  /* ── Hero banner ── */
  .hero {
    background: linear-gradient(135deg, #1A3A6C 0%, #2A5298 100%);
    border-radius: 12px; padding: 1.6rem 2rem;
    text-align: center; margin-bottom: 1.2rem;
  }
  .hero h1 { color: #CFB53B; margin: 0; font-size: 2rem; letter-spacing: 1px; }
  .hero p  { color: rgba(255,255,255,.88); margin: .4rem 0 0; font-size: .95rem; }

  /* ── Sport tabs (top row) ── */
  .sport-tab-bar {
    display: flex; gap: .6rem; flex-wrap: wrap;
    margin-bottom: 1.2rem;
  }

  /* ── Coming-soon card ── */
  .coming-soon {
    background: linear-gradient(135deg, #1A3A6C 0%, #2A5298 100%);
    border-radius: 12px; padding: 3rem 2rem;
    text-align: center; margin-top: 1rem;
  }
  .coming-soon h2 { color: #CFB53B; margin: 0 0 .6rem; font-size: 1.8rem; }
  .coming-soon p  { color: rgba(255,255,255,.85); margin: 0; font-size: 1rem; }

  /* ── Section badge ── */
  .badge {
    background: #1A3A6C; color: #CFB53B; border-radius: 5px;
    padding: .3rem .9rem; font-weight: 700; font-size: .85rem;
    display: inline-block; margin: .6rem 0 .3rem; letter-spacing: .5px;
  }

  div[data-testid="stDataFrame"] { border-radius: 6px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
import os as _os
_logo_files = ["BFHS_Logo.jpeg", "BFHS_Logo.jpg", "BFHS_logo.jpeg", "BFHS_logo.jpg", "BFHS logo.jpeg", "BFHS logo.jpg"]
_logo = next((f for f in _logo_files if _os.path.exists(f)), None)

if _logo:
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(_logo, width=110)
    with col_title:
        st.markdown("""
        <div class="hero">
          <h1>Benjamin Franklin Chargers Athletics</h1>
          <p>All-time player statistics &nbsp;·&nbsp; Queen Creek, AZ &nbsp;·&nbsp; 3A Conference</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="hero">
      <h1>Benjamin Franklin Chargers Athletics</h1>
      <p>All-time player statistics &nbsp;·&nbsp; Queen Creek, AZ &nbsp;·&nbsp; 3A Conference</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SPORT SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
sport_tab_baseball, sport_tab_bball_boys, sport_tab_bball_girls, \
    sport_tab_football, sport_tab_softball = st.tabs([
    "⚾  Baseball",
    "🏀  Boys Basketball",
    "🏀  Girls Basketball",
    "🏈  Football",
    "🥎  Softball",
])

# ═════════════════════════════════════════════════════════════════════════════
# ⚾  BASEBALL  (fully live)
# ═════════════════════════════════════════════════════════════════════════════
with sport_tab_baseball:

    EXCEL = "Franklin_Baseball_Stats.xlsx"

    @st.cache_data
    def load_baseball():
        xl = pd.ExcelFile(EXCEL)
        skip = {"Season Records"}
        data = {}
        for name in xl.sheet_names:
            if name not in skip:
                data[name] = pd.read_excel(xl, name, header=2)
        return data

    try:
        sheets    = load_baseball()
        df_rec    = sheets["Team Records"]
        df_sb     = sheets["Season Batting"]
        df_sp     = sheets["Season Pitching"]
        df_cb     = sheets["Career Batting"]
        df_cp     = sheets["Career Pitching"]
        df_lb_bat = sheets["Batting Leaderboard"]
        df_lb_pit = sheets["Pitching Leaderboard"]
        baseball_ok = True
    except Exception as e:
        st.error(f"Could not load baseball data: {e}")
        baseball_ok = False

    if baseball_ok:

        with st.expander("ℹ️  About this data", expanded=False):
            st.markdown(
                "**Stats sourced from MaxPreps official season reports.** "
                "All career totals and rate statistics (AVG, OBP, SLG, OPS, ERA, WHIP, etc.) "
                "are recalculated from raw season data. "
                "Stolen base totals were not recorded prior to the 2018-19 season.\n\n"
                "**Note on the 2019-20 season:** This season was cut short by COVID-19 and "
                "consisted of only 8 games. Stats from that year reflect a very limited sample "
                "and are not directly comparable to full seasons."
            )

        # ── Helpers ───────────────────────────────────────────────────────────
        def ip_dec(ip):
            try:
                v = float(str(ip)); w = int(v); f = round((v - w) * 10)
                return w + f / 3.0
            except:
                return 0.0

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

        # ── Baseball sub-tabs ─────────────────────────────────────────────────
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏆  Career Leaderboards",
            "📋  Season Records",
            "🔍  Player Lookup",
            "📅  Team Records",
        ])

        with tab1:
            b_tab, p_tab = st.tabs(["🏏 Batting", "⚾ Pitching"])
            with b_tab:
                st.caption("Minimum 30 AB to qualify for rate stats · click any column header to sort")
                lb = df_lb_bat.copy()
                if "Rank" in lb.columns: lb = lb.drop(columns=["Rank"])
                show_df(lb, BAT_CC)
            with p_tab:
                st.caption("Minimum 15 IP to qualify · click any column header to sort")
                lb = df_lb_pit.copy()
                if "Rank" in lb.columns: lb = lb.drop(columns=["Rank"])
                show_df(lb, PIT_CC)

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

        with tab3:
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

        with tab4:
            st.caption("All-time season records for the Chargers varsity program")
            show_df(df_rec)


# ═════════════════════════════════════════════════════════════════════════════
# 🏀  BOYS BASKETBALL  (coming soon)
# ═════════════════════════════════════════════════════════════════════════════
with sport_tab_bball_boys:
    st.markdown("""
    <div class="coming-soon">
      <h2>🏀 Boys Basketball</h2>
      <p>Stats coming soon — data is being compiled now.</p>
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 🏀  GIRLS BASKETBALL  (coming soon)
# ═════════════════════════════════════════════════════════════════════════════
with sport_tab_bball_girls:
    st.markdown("""
    <div class="coming-soon">
      <h2>🏀 Girls Basketball</h2>
      <p>Stats coming soon — data is being compiled now.</p>
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 🏈  FOOTBALL  (coming soon)
# ═════════════════════════════════════════════════════════════════════════════
with sport_tab_football:
    st.markdown("""
    <div class="coming-soon">
      <h2>🏈 Football</h2>
      <p>Stats coming soon — data is being compiled now.</p>
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 🥎  SOFTBALL  (fully live)
# ═════════════════════════════════════════════════════════════════════════════
with sport_tab_softball:

    SB_EXCEL = "Franklin_Softball_Stats.xlsx"

    @st.cache_data
    def load_softball():
        xl = pd.ExcelFile(SB_EXCEL)
        data = {}
        for name in xl.sheet_names:
            data[name] = pd.read_excel(xl, name, header=2)
        return data

    try:
        sb_sheets    = load_softball()
        sb_df_sb     = sb_sheets["Season Batting"]
        sb_df_sp     = sb_sheets["Season Pitching"]
        sb_df_cb     = sb_sheets["Career Batting"]
        sb_df_cp     = sb_sheets["Career Pitching"]
        sb_df_lb_bat = sb_sheets["Batting Leaderboard"]
        sb_df_lb_pit = sb_sheets["Pitching Leaderboard"]
        softball_ok  = True
    except Exception as e:
        st.error(f"Could not load softball data: {e}")
        softball_ok = False

    if softball_ok:

        with st.expander("ℹ️  About this data", expanded=False):
            st.markdown(
                "**Stats sourced from MaxPreps official season reports · 2016-17 through 2025-26.** "
                "Career totals and rate statistics are recalculated from raw season data. "
                "Stolen base data was not tracked in early seasons on MaxPreps.\n\n"
                "**ERA is calculated per 7 innings** (softball standard, not 9). "
                "K7 and BB7 columns represent strikeouts and walks per 7 innings.\n\n"
                "**Note:** A small number of players (particularly in early seasons) appear with "
                "truncated names on MaxPreps. These are flagged for review. Two players named "
                "C. Gordon and two named L. Elias appear in different eras — they are correctly "
                "listed as separate career entries."
            )

        def sb_nc(lbl, fmt, **kw):
            return st.column_config.NumberColumn(lbl, format=fmt, **kw)

        SB_BAT_CC = {"AVG": sb_nc("AVG","%.3f"), "OBP": sb_nc("OBP","%.3f"),
                     "SLG": sb_nc("SLG","%.3f"), "OPS": sb_nc("OPS","%.3f")}
        SB_PIT_CC = {"ERA":  sb_nc("ERA","%.2f"),  "WHIP": sb_nc("WHIP","%.3f"),
                     "K7":   sb_nc("K/7","%.1f"),   "BB7":  sb_nc("BB/7","%.1f"),
                     "WPct": sb_nc("W%","%.3f")}

        def sb_show(df, cc=None, **kw):
            st.dataframe(df.reset_index(drop=True), use_container_width=True,
                         hide_index=True, column_config=cc, **kw)

        sb_tab1, sb_tab2, sb_tab3 = st.tabs([
            "🏆  Career Leaderboards",
            "📋  Season Records",
            "🔍  Player Lookup",
        ])

        # ── Career Leaderboards ───────────────────────────────────────────────
        with sb_tab1:
            b_t, p_t = st.tabs(["🥎 Batting", "🎯 Pitching"])

            with b_t:
                st.caption("Minimum 30 career AB to qualify for rate stats · click any column header to sort")
                lb = sb_df_lb_bat.copy()
                if "Rank" in lb.columns: lb = lb.drop(columns=["Rank"])
                sb_show(lb, SB_BAT_CC)

            with p_t:
                st.caption("Minimum 15 career IP to qualify · ERA per 7 innings · click any column header to sort")
                lb = sb_df_lb_pit.copy()
                if "Rank" in lb.columns: lb = lb.drop(columns=["Rank"])
                sb_show(lb, SB_PIT_CC)

        # ── Season Records ────────────────────────────────────────────────────
        with sb_tab2:
            st.caption(
                "Best single-season performances · "
                "Batting rate stats: min 2.1 PA/game · "
                "Pitching rate stats: min 13 IP"
            )
            import math as _math

            @st.cache_data
            def sb_season_records(sb, sp, pa_factor=2.1, min_ip=13.0):
                team_games = sb.groupby("Season")["GP"].max()

                def bat_best(col):
                    s = sb.dropna(subset=[col])
                    if s.empty: return None, None, None, None
                    r = s.loc[s[col].idxmax()]
                    return r[col], r["Player"], r.get("Class"), r["Season"]

                def bat_best_qual(col):
                    mask = sb.apply(
                        lambda r: (r.get("PA", 0) or 0) >= _math.ceil(team_games.get(r["Season"], 0) * pa_factor)
                                  and (r.get("AB", 0) or 0) > 0, axis=1)
                    s = sb[mask].dropna(subset=[col])
                    if s.empty: return None, None, None, None
                    r = s.loc[s[col].idxmax()]
                    return r[col], r["Player"], r.get("Class"), r["Season"]

                def pit_best(col, df, lower=False):
                    s = df.dropna(subset=[col])
                    if s.empty: return None, None, None, None
                    r = s.loc[(s[col].idxmin() if lower else s[col].idxmax())]
                    return r[col], r["Player"], r.get("Class"), r["Season"]

                def ip_d(ip):
                    try:
                        v = float(str(ip)); w = int(v); f = round((v-w)*10)
                        return w + f/3.0
                    except: return 0.0

                spq = sp.copy()
                spq["_ip"] = spq["IP"].apply(ip_d)
                spq = spq[spq["_ip"] >= min_ip].copy()
                spq["WHIP"] = (spq["H"] + spq["BB"]) / spq["_ip"]
                spq["ERA_r"] = spq["ER"] / spq["_ip"] * 7

                recs = []
                for lbl, col in [("Home Runs","HR"),("Triples","3B"),("Doubles","2B"),
                                 ("RBIs","RBI"),("Runs Scored","R"),("Hits","H"),("Stolen Bases","SB")]:
                    if col not in sb.columns: continue
                    v, p, c, s = bat_best(col)
                    if v is not None:
                        recs.append(("BATTING", lbl, int(v), p, c, s))
                for lbl, col in [("Batting Average","AVG"),("OPS","OPS")]:
                    v, p, c, s = bat_best_qual(col)
                    if v is not None:
                        recs.append(("BATTING", f"{lbl}  (min {pa_factor} PA/game)",
                                     round(float(v),3), p, c, s))
                for lbl, col in [("Strikeouts","K"),("Wins","W")]:
                    if col not in sp.columns: continue
                    v, p, c, s = pit_best(col, sp)
                    if v is not None:
                        recs.append(("PITCHING", lbl, int(v), p, c, s))
                v, p, c, s = pit_best("ERA_r", spq, lower=True)
                if v is not None:
                    recs.append(("PITCHING", f"ERA  (min {int(min_ip)} IP)", round(float(v),2), p, c, s))
                v, p, c, s = pit_best("WHIP", spq, lower=True)
                if v is not None:
                    recs.append(("PITCHING", f"WHIP  (min {int(min_ip)} IP)", round(float(v),3), p, c, s))
                return recs

            sb_recs = sb_season_records(sb_df_sb, sb_df_sp)
            bat_r = [(c,v,p,cl,s) for sec,c,v,p,cl,s in sb_recs if sec == "BATTING"]
            pit_r = [(c,v,p,cl,s) for sec,c,v,p,cl,s in sb_recs if sec == "PITCHING"]
            RCOLS = ["Category","Record","Player","Class","Season"]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="badge">BATTING</div>', unsafe_allow_html=True)
                sb_show(pd.DataFrame(bat_r, columns=RCOLS),
                        {"Record": st.column_config.NumberColumn("Record", format="%.3f")})
            with c2:
                st.markdown('<div class="badge">PITCHING</div>', unsafe_allow_html=True)
                sb_show(pd.DataFrame(pit_r, columns=RCOLS),
                        {"Record": st.column_config.NumberColumn("Record", format="%.3f")})

        # ── Player Lookup ─────────────────────────────────────────────────────
        with sb_tab3:
            sb_cb_ids = sb_df_cb[["Player","GradYr"]].copy()
            sb_cp_ids = sb_df_cp[["Player","GradYr"]].copy()
            sb_all_pl = (pd.concat([sb_cb_ids, sb_cp_ids])
                           .drop_duplicates()
                           .sort_values("Player")
                           .reset_index(drop=True))

            def sb_pl_label(row):
                try:
                    gy = int(row["GradYr"])
                    return f"{row['Player']}  (Grad '{str(gy)[-2:]})"
                except:
                    return str(row["Player"])

            sb_option_map = {sb_pl_label(r): (r["Player"], r["GradYr"])
                             for _, r in sb_all_pl.iterrows()}

            sb_sel = st.selectbox(
                "Search for a player:",
                list(sb_option_map.keys()),
                index=None,
                placeholder="Start typing a name…",
                key="sb_player_select",
            )

            if sb_sel:
                name, gy = sb_option_map[sb_sel]

                def sb_match(df):
                    nm = df["Player"] == name
                    if pd.isna(gy):
                        return df[nm]
                    try:
                        return df[nm & (df["GradYr"].fillna(-1).astype(int) == int(gy))]
                    except:
                        return df[nm]

                sb_rows = sb_match(sb_df_sb)
                sp_rows = sb_match(sb_df_sp)
                cb_rows = sb_match(sb_df_cb)
                cp_rows = sb_match(sb_df_cp)

                gy_str = f"  ·  Grad '{str(int(gy))[-2:]}" if pd.notna(gy) else ""
                st.markdown(f"### {name}{gy_str}")
                st.markdown("---")

                if not sb_rows.empty:
                    BAT_COLS = ["Season","Class","GP","AVG","PA","AB","R","H","RBI",
                                "2B","3B","HR","BB","K","HBP","OBP","SLG","OPS","SB"]
                    BAT_COLS = [c for c in BAT_COLS if c in sb_rows.columns]
                    st.markdown("**Season Batting**")
                    sb_show(sb_rows[BAT_COLS], SB_BAT_CC)
                    if not cb_rows.empty:
                        CAR = ["GP","AVG","PA","AB","R","H","RBI","2B","3B","HR",
                               "BB","K","HBP","SB","OBP","SLG","OPS"]
                        CAR = [c for c in CAR if c in cb_rows.columns]
                        st.markdown("**Career Batting Totals**")
                        sb_show(cb_rows[CAR], SB_BAT_CC)

                if not sp_rows.empty:
                    PIT_COLS = ["Season","Class","ERA","W","L","APP","GS","CG","SV",
                                "IP","H","R","ER","BB","K"]
                    PIT_COLS = [c for c in PIT_COLS if c in sp_rows.columns]
                    st.markdown("**Season Pitching**")
                    sb_show(sp_rows[PIT_COLS], SB_PIT_CC)
                    if not cp_rows.empty:
                        CAR_P = ["ERA","W","L","WPct","APP","GS","CG","SV",
                                 "IP","H","R","ER","BB","K","K7","BB7","WHIP"]
                        CAR_P = [c for c in CAR_P if c in cp_rows.columns]
                        st.markdown("**Career Pitching Totals**")
                        sb_show(cp_rows[CAR_P], SB_PIT_CC)

                if sb_rows.empty and sp_rows.empty:
                    st.info("No season data found for this player.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Stats sourced from MaxPreps official season reports  ·  "
    "Career totals and rate stats recalculated from raw season data  ·  "
    "2019-20 baseball season COVID-shortened (8 games)  ·  "
    "Benjamin Franklin High School, Queen Creek AZ"
)
