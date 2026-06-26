import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "publish_article.py"
)

spec = importlib.util.spec_from_file_location("publish_article", SCRIPT_PATH)
publish_article = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_article)


def test_replace_picsum_with_wechat_urls_replaces_complete_src():
    html = (
        '<div style="font-family:Georgia,宋体,serif;">'
        '<img src="https://picsum.photos/seed/abc/600/400" style="x">'
        '<img src="https://picsum.photos/seed/def/600/400" style="y">'
        "</div>"
    )

    result = publish_article.replace_picsum_with_wechat_urls(
        html,
        [
            "http://mmbiz.qpic.cn/one",
            "https://mmbiz.qpic.cn/two",
        ],
    )

    assert 'src="http://mmbiz.qpic.cn/one"' in result
    assert 'src="https://mmbiz.qpic.cn/two"' in result
    assert "picsum.photos" not in result
    assert "abc/600/400" not in result
    assert "def/600/400" not in result
    assert 'style="x"' in result
    assert 'style="y"' in result


def test_replace_picsum_with_wechat_urls_rejects_non_wechat_cdn_url():
    html = (
        '<div style="font-family:Georgia,宋体,serif;">'
        '<img src="https://picsum.photos/seed/abc/600/400" style="x">'
        "</div>"
    )

    try:
        publish_article.replace_picsum_with_wechat_urls(
            html, ["https://example.com/image.jpg"]
        )
    except ValueError as exc:
        assert "Invalid WeChat CDN URL" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_normalize_article_meta_uses_utf8_byte_limits():
    title = "《AI取经记》" * 20
    digest = "这是一段微信公众号摘要，需要按字节稳定截断。" * 20

    normalized_title, normalized_digest = publish_article.normalize_article_meta(
        title, digest
    )

    assert len(normalized_title.encode("utf-8")) <= 55
    assert len(normalized_digest.encode("utf-8")) <= 115


def test_parse_article_html_and_insertion_points_are_deterministic():
    html = (
        '<div style="font-family:Georgia,宋体,serif;">'
        '<p>第一段</p>'
        '<p style="font-size:18px;color:#888;border-top:1px solid #ddd;'
        'padding-top:16px;margin-bottom:6px;">一、开头</p>'
        '<p>第二段</p>'
        '<p style="font-size:18px;color:#888;border-top:1px solid #ddd;'
        'padding-top:16px;margin-bottom:6px;">二、展开</p>'
        '<p>第三段</p>'
        "</div>"
    )

    parsed = publish_article.parse_article_html(html)
    positions = publish_article.find_insertion_points(
        parsed, body_image_count=2
    )

    assert len(parsed["chapters"]) == 2
    assert len(positions) == 3
    assert positions[0] == parsed["chapters"][0].start()
    assert positions[1] == parsed["chapters"][1].start()


def test_parse_publish_params_normalizes_intent_fields():
    article = "# 一个很长的标题" + "标题" * 40 + "\n\n第一段摘要内容。"

    params = publish_article.parse_publish_params(
        article_md=article,
        cover_seed=" cover ",
        body_seeds=" road, , sky ",
        author="",
    )

    assert len(params["title"].encode("utf-8")) <= 55
    assert len(params["digest"].encode("utf-8")) <= 115
    assert params["cover_seed"] == "cover"
    assert params["body_seeds"] == ["road", "sky"]
    assert params["author"] == "王波"


def test_markdown_to_wechat_html_renders_without_ai():
    article = (
        "# 标题\n\n"
        "第一段正文。\n\n"
        "## 一、章节\n\n"
        "第二段有 **重点** 和 `code`。"
    )

    html = publish_article.markdown_to_wechat_html(article)

    assert html.startswith("<div ")
    assert "<img" not in html
    assert "标题" not in html
    assert "一、章节" in html
    assert "<strong>重点</strong>" in html
    assert "<code>code</code>" in html


def test_publish_workflow_dry_run_skips_external_services():
    article = (
        "# 测试标题\n\n"
        "第一段正文。\n\n"
        "## 一、章节\n\n"
        "第二段正文。\n\n"
        "## 二、章节\n\n"
        "第三段正文。"
    )

    result = publish_article.publish_workflow(
        article_md=article,
        cover_seed="cover",
        body_seeds=["body1", "body2"],
        appid="",
        secret="",
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["layout_provider"] == "deterministic"
    assert result["draft_media_id"] == "dry_run_draft_media_id"
    assert result["image_count"] == 3
    assert "picsum.photos" not in result["final_html"]
    assert result["final_html"].count("mmbiz.qpic.cn/dry-run") == 3
