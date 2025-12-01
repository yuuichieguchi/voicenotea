#!/usr/bin/env python3
"""
10インチタブレット用スクリーンショット生成スクリプト
モバイルスクリーンショットを拡大してタブレット対応画像を作成します
"""

import os
from PIL import Image

# 設定
MOBILE_SCREENSHOTS_DIR = "/Users/eguchiyuuichi/projects/voicenotea/docs/mobile_screenshots"
OUTPUT_DIR = "/Users/eguchiyuuichi/projects/voicenotea/docs/tablet_10inch_screenshots"

# 10インチタブレットの標準解像度 (9:16 縦向き)
TABLET_WIDTH = 1080
TABLET_HEIGHT = 1920

# モバイルスクリーンショットのファイル
MOBILE_SCREENSHOTS = [
    "Screenshot_20251202_011318_Voicenotea.jpg",
    "Screenshot_20251202_011324_Voicenotea.jpg",
    "Screenshot_20251202_011338_Voicenotea.jpg",
    "Screenshot_20251202_011540_Voicenotea.jpg",
    "Screenshot_20251202_012104_Voicenotea.jpg",
]


def create_output_dir():
    """出力ディレクトリを作成"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"出力ディレクトリを作成しました: {OUTPUT_DIR}")


def get_target_dimensions(original_width, original_height):
    """
    元の画像のアスペクト比を維持しながら、
    タブレット解像度に合わせたサイズを計算
    """
    original_aspect = original_width / original_height

    # 元の画像が縦向き (アスペクト比 < 1)
    if original_aspect < 1:
        # 高さを基準にしてスケール
        target_height = TABLET_HEIGHT
        target_width = int(target_height * original_aspect)

        # 幅がタブレット幅を超える場合、幅を基準に
        if target_width > TABLET_WIDTH:
            target_width = TABLET_WIDTH
            target_height = int(target_width / original_aspect)
    else:
        # 横向きの場合、幅を基準にしてスケール
        target_width = TABLET_WIDTH
        target_height = int(target_width / original_aspect)

        # 高さがタブレット高さを超える場合、高さを基準に
        if target_height > TABLET_HEIGHT:
            target_height = TABLET_HEIGHT
            target_width = int(target_height * original_aspect)

    return target_width, target_height


def create_tablet_screenshot(mobile_path, output_path):
    """
    モバイルスクリーンショットをタブレット用に拡大
    アスペクト比を維持し、レターボックスを追加
    """
    # 元画像を開く
    mobile_img = Image.open(mobile_path)
    mobile_width, mobile_height = mobile_img.size

    print(f"\n処理中: {os.path.basename(mobile_path)}")
    print(f"  元のサイズ: {mobile_width}x{mobile_height}")

    # ターゲットサイズを計算
    target_width, target_height = get_target_dimensions(mobile_width, mobile_height)
    print(f"  拡大後のサイズ: {target_width}x{target_height}")

    # 高品質で拡大 (LANCZOS フィルタを使用)
    resized_img = mobile_img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # タブレット用キャンバスを作成 (背景色は黒)
    tablet_img = Image.new('RGB', (TABLET_WIDTH, TABLET_HEIGHT), color=(0, 0, 0))

    # リサイズされた画像をキャンバスの中央に配置
    x_offset = (TABLET_WIDTH - target_width) // 2
    y_offset = (TABLET_HEIGHT - target_height) // 2
    tablet_img.paste(resized_img, (x_offset, y_offset))

    # JPEG形式で保存 (品質95で高品質を維持)
    tablet_img.save(output_path, 'JPEG', quality=95, optimize=True)

    # ファイルサイズを確認
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  出力サイズ: {target_width}x{target_height}")
    print(f"  ファイルサイズ: {file_size_mb:.2f} MB")

    if file_size_mb > 8:
        print("  警告: ファイルサイズが8MBを超えています")


def main():
    """メイン処理"""
    print("=" * 60)
    print("10インチタブレット用スクリーンショット生成ツール")
    print("=" * 60)
    print(f"入力ディレクトリ: {MOBILE_SCREENSHOTS_DIR}")
    print(f"出力ディレクトリ: {OUTPUT_DIR}")
    print(f"ターゲット解像度: {TABLET_WIDTH}x{TABLET_HEIGHT} (9:16)")
    print("=" * 60)

    # 出力ディレクトリを作成
    create_output_dir()

    # 各スクリーンショットを処理
    for filename in MOBILE_SCREENSHOTS:
        input_path = os.path.join(MOBILE_SCREENSHOTS_DIR, filename)

        if not os.path.exists(input_path):
            print(f"\n警告: ファイルが見つかりません: {filename}")
            continue

        # 出力ファイル名を生成
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_10inch_tablet.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # タブレット用スクリーンショットを作成
        create_tablet_screenshot(input_path, output_path)

    print("\n" + "=" * 60)
    print("完了しました！")
    print(f"生成されたファイル: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
