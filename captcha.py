import sys
import cv2
import geetest_captcha_v3_icon_analysis
from PIL import Image


def geetest_captcha_v3_icon_analysis_detection_tip(image_path, path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    _, padded_img, result_boxes = geetest_captcha_v3_icon_analysis.detection_tip(img)
    i = 0
    result_boxes = sorted(result_boxes, key=lambda box: box[0])
    boxes = []
    for box in result_boxes:
        x1, y1, x2, y2, _ = box
        boxes.append((x1, y1, x2, y2))
        cv2.imwrite(path + str(i) + ".jpg", padded_img[y1:y2, x1:x2])
        i += 1
    return boxes


def geetest_captcha_v3_icon_analysis_detection_item(image_path, path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    _, result_boxes = geetest_captcha_v3_icon_analysis.detection_item(img)
    i = 0
    result_boxes = sorted(result_boxes, key=lambda box: box[0])
    boxes = []
    for box in result_boxes:
        x1, y1, x2, y2, _ = box
        boxes.append((x1, y1, x2, y2))
        cv2.imwrite(path + str(i) + ".jpg", img[y1:y2, x1:x2])
        i += 1
    return boxes


def geetest_captcha_v3_icon_analysis_calculate_similarity(image_path1, image_path2):
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)
    result = geetest_captcha_v3_icon_analysis.calculate_similarity(img1, img2)
    return float(result)


def cracker(
    tip_image,
    img_image,
    path,
):
    tip_poses = geetest_captcha_v3_icon_analysis_detection_tip(
        tip_image, path + "/" + "tip_"
    )
    img_poses = geetest_captcha_v3_icon_analysis_detection_item(
        img_image, path + "/" + "img_"
    )
    tip_nums = len(tip_poses)
    img_nums = len(img_poses)
    click_results = []
    used_indices = set()
    for i in range(tip_nums):
        max_similarity = -sys.float_info.max
        img_index = 0
        for j in range(img_nums):
            if j in used_indices:
                continue
            similarity_result = geetest_captcha_v3_icon_analysis_calculate_similarity(
                path + "/" + "tip_" + str(i) + ".jpg",
                path + "/" + "img_" + str(j) + ".jpg",
            )
            if similarity_result > max_similarity:
                max_similarity = similarity_result
                img_index = j
        click_results.append(img_poses[img_index])
        used_indices.add(img_index)
    return click_results
