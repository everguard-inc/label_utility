import json
from typing import Dict, List, NoReturn, Union

import config as cfg


class Point:
    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y


class BBox:
    def __init__(self, x1: int, y1: int, x2: int, y2: int, label: cfg.ClassLabel):
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2
        self.label: cfg.ClassLabel = label

    def __contains__(self, item: Point):
        if self.x1 <= item.x <= self.x2 and self.y1 <= item.y <= self.y2:
            return True
        return False


class Annotation:
    def __init__(self):
        self._images_info_list: List[Dict] = list()
        self._images_info_dict: Dict[str, List[BBox]] = dict()

    @property
    def images_amount(self):
        return len(self._images_info_list)

    def open_coco_annotation(self, annotation_path: str) -> NoReturn:

        with open(annotation_path, "r") as jfile:
            coco_ann = json.load(jfile)

        images = coco_ann["images"]
        categories = coco_ann["categories"]
        labels = coco_ann["annotations"]

        image_dict = dict()
        category_dict = dict()

        # images
        for image_info in images:
            image_dict[image_info["id"]] = image_info["file_name"]

            self._images_info_dict[image_info["file_name"]] = list()

        # categories
        for category_info in categories:
            category_name = category_info["name"]

            if category_name in cfg.misspelling_correction:
                category_name = cfg.misspelling_correction[category_name]

            category_dict[category_info["id"] - 1] = {
                "class_name": category_name,
            }

        # labels
        for i, label_info in enumerate(labels):

            x1 = label_info["bbox"][0]
            y1 = label_info["bbox"][1]
            w = label_info["bbox"][2]
            h = label_info["bbox"][3]

            image_name = image_dict[label_info["image_id"]]

            cat_id = label_info["category_id"]
            self._images_info_dict[image_name].append(
                BBox(
                    x1,
                    y1,
                    x1 + w,
                    y1 + h,
                    cfg.CATEGORY_ID_TO_LABEL[label_info["category_id"]],
                )
            )

        # converting image dict to list
        for image_name, bbox_list in self._images_info_dict.items():
            self._images_info_list.append(
                {
                    "image_name": image_name,
                    "bboxes": bbox_list,
                }
            )

        # sort by image name
        self._images_info_list.sort(key=lambda x: x["image_name"])

    def get_bboxes_for_image(self, image_id: int) -> List[BBox]:
        return self._images_info_list[image_id]["bboxes"]

    def get_image_name_by_id(self, image_id: int) -> str:
        return self._images_info_list[image_id]["image_name"]

    def get_sorted_images_names(self) -> List[str]:
        return [image_name["image_name"] for image_name in self._images_info_list]

    def get_bboxes_by_image_name(self, img_name: str) -> Union[List[BBox], None]:
        if img_name in self._images_info_dict:
            return self._images_info_dict[img_name]
        return None
