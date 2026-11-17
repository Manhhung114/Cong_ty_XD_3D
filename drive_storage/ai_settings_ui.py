"""Admin-only native provider configuration, shared across all verified staff.

Credentials are never rendered into the inline app, the browser, or logs.
"""
from __future__ import annotations

from drive_storage.access_control import identity_for, can_admin
from drive_storage.ai_vault import (
    effective_config, read_shared, save_shared, revoke_shared, PROVIDERS,
)
from drive_storage.manager import from_streamlit_secrets
from drive_storage.company_agents import agents
from drive_storage.ai_probe import probe_ai_connection


def ai_settings_dialog(st):
    @st.dialog("Cấu hình AI toàn công ty · V6.7.6", width="large")
    def render():
        identity = identity_for(st)
        if not can_admin(identity):
            st.error("Chỉ Admin đã xác thực mới được quản lý API dùng chung.")
            return
        try:
            storage = from_streamlit_secrets(dict(st.secrets.get("drive", {})))
            secret = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
            file_id, shared = read_shared(storage, secret)
            current = shared or dict(st.secrets.get("ai", {}))
        except (PermissionError, RuntimeError, ValueError) as exc:
            st.error(str(exc))
            st.warning("Kho có lỗi không được ghi đè. Hãy khôi phục khóa máy chủ cũ.")
            return
        except Exception:
            st.error("Không kết nối được kho cấu hình trên Google Drive.")
            return

        if st.button("Đóng", key="v676_ai_close"):
            st.session_state.drive_in_app_action = None
            st.rerun()
            return

        st.info(
            "API key lưu mã hóa trên Google Drive, chỉ máy chủ giải mã. "
            "Admin chỉ nhập một lần; các nhân viên được cấp quyền sử dụng AI "
            "mà không thấy hoặc nhập lại khóa. Lượt chạy chỉ phát sinh khi "
            "người dùng chủ động chọn Chạy Agent và đồng ý gửi metadata/file mẫu."
        )
        st.write(
            "**Trạng thái:** " +
            ("Đã lưu mã hóa trên Drive cho toàn công ty" if shared else
             "Chưa lưu trên Drive (đang dùng cấu hình máy chủ cũ nếu có)")
        )
        profiles = agents()
        ids = list(profiles)
        names = {aid: profiles[aid]["title"] for aid in ids}
        old_provider = str(current.get("provider") or "gemini").lower()
        if old_provider not in PROVIDERS:
            old_provider = "gemini"
        old_model = str(current.get("model") or "")
        overrides = dict(current.get("agent_models") or {})
        with st.form("v676_shared_ai_config"):
            provider = st.selectbox(
                "Nhà cung cấp AI dùng chung", ["gemini", "openai"],
                index=["gemini", "openai"].index(old_provider),
                format_func=lambda p: "Google Gemini" if p == "gemini" else "OpenAI",
            )
            model = st.text_input(
                "Model mặc định của 18 Agent", value=old_model,
                placeholder="Ví dụ: gemini-2.5-flash hoặc gpt-4.1-mini",
                max_chars=100,
            )
            key = st.text_input(
                "API key – chỉ nhập khi thiết lập/thay khóa",
                type="password", value="",
                max_chars=500,
                help="Không hiển thị lại khóa đã lưu. Để trống khi giữ khóa hiện có cùng nhà cung cấp.",
            )
            agent_id = st.selectbox(
                "Tùy chọn model riêng cho một Agent", ["", *ids],
                format_func=lambda a: "— Cả 18 Agent dùng model mặc định —"
                if not a else names[a] + " (" + a + ")",
            )
            agent_model = st.text_input(
                "Model riêng (để trống nếu dùng model mặc định)",
                value="", max_chars=100,
            )
            consent = st.checkbox(
                "Tôi xác nhận đây là API dùng chung do công ty quản lý; "
                "có thể phát sinh chi phí khi nhân viên chạy AI.",
                value=False,
            )
            check = st.form_submit_button("🔎 Kiểm tra kết nối API", type="secondary")
            save = st.form_submit_button("Lưu mã hóa và áp dụng toàn công ty",
                                         type="primary")
        st.caption(
            "Mỗi lần lưu thay thế cấu hình chung. Nếu đã có model tùy chỉnh "
            "cho Agent khác, hệ thống giữ các tùy chỉnh đó. Muốn sửa model riêng "
            "hãy chọn đúng Agent và nhập mã mới."
        )
        if check:
            try:
                test_key = key.strip()
                if not test_key and str(current.get("provider") or "").lower() == provider:
                    test_key = str(current.get("api_key") or "")
                if not test_key:
                    raise ValueError("Chưa có API key cho nhà cung cấp đang chọn. Hãy nhập khóa để kiểm tra.")
                test_model = (agent_model.strip() or overrides.get(agent_id) or model) if agent_id else model
                result = probe_ai_connection(provider, test_model, test_key)
                if result["ok"]:
                    st.success(result["message"] + " · " + provider + " / " + test_model)
                else:
                    st.error(result["message"])
                st.caption("Đã kiểm tra trực tuyến từ máy chủ, không lưu khóa vừa nhập, không gọi AI sinh nội dung.")
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Chưa kiểm tra được kết nối; cấu hình đã lưu không bị thay đổi.")

        if save:
            try:
                if not consent:
                    raise PermissionError("Cần xác nhận quyền và chi phí sử dụng API.")
                chosen_key = key.strip()
                if not chosen_key:
                    if str(current.get("provider") or "").lower() != provider:
                        raise ValueError("Đổi nhà cung cấp phải nhập API key mới.")
                    chosen_key = str(current.get("api_key") or "")
                if not chosen_key:
                    raise ValueError("Chưa có API key để lưu dùng chung.")
                selected = dict(overrides)
                if agent_id:
                    if agent_model.strip():
                        selected[agent_id] = agent_model.strip()
                    else:
                        selected.pop(agent_id, None)
                save_shared(
                    storage, secret, identity, provider=provider, model=model,
                    api_key=chosen_key, agent_models=selected,
                )
                st.session_state.drive_in_app_action = None
                st.toast("Đã lưu cấu hình AI mã hóa trên Drive. Tất cả phiên đăng nhập tiếp theo dùng chung.")
                st.rerun()
            except (ValueError, PermissionError, RuntimeError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không lưu được cấu hình AI, dữ liệu cũ vẫn được giữ nguyên.")

        if shared:
            st.divider()
            st.warning(
                "Thu hồi khóa sẽ vô hiệu hóa API dùng chung. Lệnh Agent đã chạy "
                "và lịch sử báo cáo trên Drive vẫn được giữ nguyên."
            )
            confirm = st.checkbox("Xác nhận thu hồi API dùng chung", key="v676_revoke_confirm")
            if st.button("Thu hồi khóa AI khỏi Drive", disabled=not confirm):
                try:
                    revoke_shared(storage, identity, secret)
                    st.session_state.drive_in_app_action = None
                    st.toast("Đã thu hồi API dùng chung.")
                    st.rerun()
                except Exception:
                    st.error("Không thu hồi được. Vui lòng kiểm tra quyền quản trị Drive.")

    render()


def ai_connection_dialog(st):
    """Read-only one-click check of the saved server credential (Admin only)."""
    @st.dialog("🔎 Kiểm tra kết nối API dùng chung", width="large")
    def render():
        if not can_admin(identity_for(st)):
            st.error("Chỉ Admin đã xác thực được kiểm tra khóa API dùng chung.")
            return
        if st.button("Đóng", key="v677_api_check_close"):
            st.session_state.drive_in_app_action = None
            st.session_state.pop("v677_api_probe_pending", None)
            st.session_state.pop("v677_api_probe_result", None)
            st.rerun()
            return
        try:
            current = effective_config(st)
            provider = str(current.get("provider") or "").lower()
            model = str(current.get("model") or "")
            key = str(current.get("api_key") or "")
        except Exception:
            st.error("Không đọc được khóa API trên máy chủ. Kiểm tra kho mã hóa Google Drive.")
            return
        if provider not in PROVIDERS or not model or not key:
            st.warning("Chưa cấu hình API hợp lệ. Hãy vào Cài đặt / Thay API dùng chung để nhập khóa và model.")
            return
        label = "Google Gemini" if provider == "gemini" else "OpenAI"
        st.write("**Nhà cung cấp:** " + label + " · **Model:** " + model)
        st.caption("Kiểm tra trực tiếp quyền truy cập thông tin model từ máy chủ. "
                   "Không tạo nội dung AI, không thay đổi API key hoặc dữ liệu trên Drive.")
        run = bool(st.session_state.pop("v677_api_probe_pending", False))
        if st.button("🔎 Kiểm tra lại", key="v677_api_check_retry", type="primary"):
            run = True
        if run:
            try:
                result = probe_ai_connection(provider, model, key)
            except ValueError:
                result = {"ok": False, "message": "Cấu hình API key hoặc model không hợp lệ."}
            except Exception:
                result = {"ok": False, "message": "Không kiểm tra được kết nối nhà cung cấp AI."}
            # Never retain plaintext keys or provider error bodies in session.
            st.session_state.v677_api_probe_result = result
        result = st.session_state.get("v677_api_probe_result")
        if isinstance(result, dict):
            if result.get("ok"):
                st.success("Kết nối thành công: " + result["message"])
            else:
                st.error("Chưa kết nối thành công: " + str(result.get("message") or "Lỗi không xác định"))
        st.caption("Kết quả chỉ phản ánh trạng thái kiểm tra tại thời điểm nhấn nút. "
                   "Không bảo đảm hạn mức tạo nội dung AI, chi phí hoặc khả năng chạy Agent sau này.")

    render()
