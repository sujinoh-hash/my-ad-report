  st.header("🔄 GA4 TSV → Excel 변환")
    st.caption("GA4에서 다운받은 TSV 파일을 업로드하면 Excel(.xlsx)로 변환해드려요.")
 
    tsv_files = st.file_uploader(
        "GA4 TSV 파일들을 드래그하세요.",
        type=["tsv", "txt"], accept_multiple_files=True, key="t4"
    )
 
    if tsv_files:
        for f in tsv_files:
            st.divider()
            st.markdown(f"**📄 {f.name}**")
            try:
                raw_bytes = f.read()
                df = parse_ga4_tsv(raw_bytes)
 
                # 캠페인명 변환 컬럼 추가
                if "세션캠페인" in df.columns:
                    df.insert(
                        df.columns.get_loc("세션캠페인") + 1,
                        "AI_제안명",
                        df.apply(
                            lambda r: build_campaign_key_ga4(
                                r["세션캠페인"],
                                r.get("세션검색어", ""),
                                r.get("세션광고콘텐츠", "")
                            ), axis=1
                        )
                    )
                    unk_cnt = (df["AI_제안명"] == "Unknown").sum()
                    st.info(f"✅ {len(df)}행 | ⚠️ Unknown: {unk_cnt}행")
 
                st.dataframe(df.head(500))
 
                # Excel 변환 후 다운로드
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="GA4 데이터")
 
                out_name = f.name.rsplit(".", 1)[0] + ".xlsx"
                st.download_button(
                    f"📥 {out_name} 다운로드",
                    data=out.getvalue(),
                    file_name=out_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{f.name}",
                )
 
            except Exception as e:
                st.error(f"❌ 오류: {e}")
 
