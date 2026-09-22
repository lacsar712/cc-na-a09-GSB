def judge(measured_cd: float, required_cd: float, bearing_error_deg: float) -> tuple[str, str]:
    if measured_cd < required_cd:
        return "不合格", "光强不足"
    if abs(bearing_error_deg) > 2:
        return "不合格", "方位偏差过大"
    return "合格", "光强与方位均在限内"


def tag_rejection(measured_cd: float, section) -> str:
    """贴标校验：实测光强低于区段标称亮度下限则返回拒绝原因，否则返回空串。"""
    if measured_cd < section.min_cd:
        return (
            f"实测光强 {measured_cd:g} 低于区段「{section.name}」"
            f"标称亮度下限 {section.min_cd:g}，不允许贴标"
        )
    return ""
