import argparse
import json
import os
import sys
from copy import deepcopy

from typing import Union, List, Dict, NoReturn

import cv2
import numpy as np

import config as cfg
from data_structures import BBox, Point


class AnnotationStorage:

    def __init__(self, annotations: str, output_folder: str, image_folder: str, start_frame_id: str=None):

        self._images_folder: str = image_folder
        self._output_folder: str = output_folder
        self._dir_skipped = os.path.join(self._output_folder, cfg.DIRECTORY_FOR_SKIPPED_NAME)
        self._dir_labeled = os.path.join(self._output_folder, cfg.DIRECTORY_FOR_LABELED_NAME)

        self._variables_file_path = os.path.join(os.path.dirname(annotations), cfg.VARIABLES_FILE_NAME)

        self._images_info_list: List[Dict] = list()
        self._images_info_dict: Dict[str, List[BBox]] = dict()
        self._open_annotations(annotations)

        self._current_image_id: int = self._set_start_frame_id(start_frame_id)

    @property
    def current_image_name(self):
        return self._images_info_list[self._current_image_id]['image_name']

    @property
    def images_amount(self):
        return len(self._images_info_list)

    @property
    def current_image_id(self):
        return self._current_image_id

    @property
    def current_bboxes(self):
        return self._images_info_list[self._current_image_id]["bboxes"]

    def get_bboxes_by_image_id(self, image_id: int) -> Union[List[BBox], None]:
        if image_id < len(self._images_info_list):
            return self._images_info_list[image_id]["bboxes"]
        return None

    def get_bboxes_by_image_name(self, img_name: str) -> Union[List[BBox], None]:
        if img_name in self._images_info_dict:
            return self._images_info_dict[img_name]
        return None

    def get_image_name_by_id(self, image_id: int) -> str:
        return self._images_info_list[image_id]["image_name"]

    def get_sorted_images_names(self) -> List[str]:
        return [image_name["image_name"] for image_name in self._images_info_list]

    def change_current_image_id(self, direction, step):
        self._update_current_image_id(direction, step)

    def _open_annotations(self, annotation_path):
        self._open_coco_annotation(annotation_path)

    def _set_start_frame_id(self, frame_id: Union[int, str]):
        # try to open user specified index
        if frame_id is not None:
            frame_id = int(frame_id)
            if 0 <= frame_id < self.images_amount:
                return frame_id
        else:
            print('Frame with specified id not exist')
        
        # try to open previously saved index in json file
        if os.path.isfile(self._variables_file_path):
            with open(self._variables_file_path, 'r') as json_file:
                values = json.load(json_file)
            if cfg.PresistentVariableName.IMAGE_ID in values:
                return int(values[cfg.PresistentVariableName.IMAGE_ID])
            
        # return first image index
        return 0
    
    def _save_image_id_to_variables_file(self):
        with open(self._variables_file_path, 'w') as json_file:
            json.dump({cfg.PresistentVariableName.IMAGE_ID: self.current_image_id}, json_file)

    def _update_current_image_id(self, direction: bool, step: int):
        new_image_id = (
            self._current_image_id + step
            if direction
            else self._current_image_id - step
        )

        if new_image_id > self.images_amount:
            new_image_id = self.images_amount - 1
        elif new_image_id < 0:
            new_image_id = 0
        self._current_image_id = new_image_id

        self._save_image_id_to_variables_file()

    def _open_coco_annotation(self, annotation_path: str) -> NoReturn:

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



class Canvas:
    """Works with graphics"""

    def __init__(self):
        self._bboxes: List[BBox]
        self._current_image: np.ndarray
        self._mode: cfg.LabelingMode = cfg.LabelingMode.DRAWING
        self._clear_image: np.ndarray
        self._selected_class_label: cfg.ClassLabel = cfg.DEFAULT_CLASS_LABEL
        self._render_with_id: bool = False
        self._state: cfg.CanvasState = cfg.CanvasState.NORMAL
        # used to select bbox id using keyboard. Dict[number_on_keyboard: bbox_id]
        self._keyboard_key_to_bbox_id_mapper: Dict[int, int] = dict()
        cv2.namedWindow(cfg.WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(cfg.WINDOW_NAME, self._on_mouse)
        cv2.resizeWindow(cfg.WINDOW_NAME, 900, 600)

    @property
    def state(self):
        return self._state

    def specify_bbox(self, number: int):

        if number not in self._keyboard_key_to_bbox_id_mapper:
            print(f'select number from list {list(self._keyboard_key_to_bbox_id_mapper.keys())}')
            return

        bbox_id = self._keyboard_key_to_bbox_id_mapper[number]

        if self._mode == cfg.LabelingMode.DELETION:
            self._delete_bbox_by_id(bbox_id)
        elif self._mode == cfg.LabelingMode.SET_LABEL:
            self._set_label_to_bbox_by_id(bbox_id)

        self._change_state(cfg.CanvasState.NORMAL)
        self._clear_keyboard_key_to_bbox_id_mapper()
        self.refresh()

    def set_mode(self, mode: cfg.LabelingMode):
        self._mode = mode

    def set_image(self, img: np.ndarray):
        self._clear_image = img

    def refresh(self):
        self._render_bboxes(self._bboxes)
        self._turn_off_render_with_id()

    def set_class_label(self, class_label: cfg.ClassLabel):
        self._selected_class_label = class_label

    def get_bboxes_json(self):
        bboxes_list = list()
        for bbox in self._bboxes:
            bboxes_list.append(
                [bbox.x1, bbox.y1, bbox.x2, bbox.y2, cfg.LABEL_CATEGORY_ID[bbox.label]]
            )
        return bboxes_list

    def set_bboxes(self, bboxes):
        self._bboxes = deepcopy(bboxes)

    def draw_bbox(self):
        region = cv2.selectROI(cfg.WINDOW_NAME, self._current_image)
        cv2.setMouseCallback(cfg.WINDOW_NAME, self._on_mouse)

        y1 = int(region[1])
        y2 = int(region[1] + region[3])
        x1 = int(region[0])
        x2 = int(region[0] + region[2])

        self._bboxes.append(BBox(x1, y1, x2, y2, self._selected_class_label))
        print(f"bbox with class {self._selected_class_label} created")

        self.refresh()

    def _on_mouse(self, event, x, y, flags, param):
        point = Point(x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.state == cfg.CanvasState.NORMAL:
                if self._mode == cfg.LabelingMode.DELETION:
                    self._delete_bbox_contains_point(point)
                if self._mode == cfg.LabelingMode.SET_LABEL:
                    self._set_label_to_bbox_contains_point(point)
                self.refresh()

    def _delete_bbox_by_id(self, bbox_id: int):
        if len(self._bboxes) > bbox_id:
            del self._bboxes[bbox_id]
        else:
            print('no element with this id')

    def _delete_bbox_contains_point(self, point: Point):
        bbox_id = self._get_selected_bbox_id(point)
        if bbox_id is not None:
            self._delete_bbox_by_id(bbox_id)
            print(f"bbox with id {bbox_id} deleted")

    def _set_label_to_bbox_by_id(self, bbox_id: int):
        if len(self._bboxes) > bbox_id:
            self._bboxes[bbox_id].label = self._selected_class_label
        else:
            print('no element with this id')

    def _set_label_to_bbox_contains_point(self, point: Point):
        bbox_id = self._get_selected_bbox_id(point)
        if bbox_id is not None:
            self._set_label_to_bbox_by_id(bbox_id)
            print(f"set label {self._selected_class_label} for bbox with id {bbox_id}")

    def _clear_keyboard_key_to_bbox_id_mapper(self):
        self._keyboard_key_to_bbox_id_mapper = dict()

    def _get_selected_bbox_id(self, point: Point) -> Union[int, None]:
        selected_id = list()
        for i, bbox in enumerate(self._bboxes):
            if point in bbox:
                selected_id.append(i)

        # if clicked on more than one bbox simultaneously
        if len(selected_id) > 1:
            print('selected bboxes with id: ', selected_id)
            self._change_state(cfg.CanvasState.ASK_BBOX_INDEX)
            self._turn_on_render_with_id()

            # update which keyboard number matches bbox id
            self._clear_keyboard_key_to_bbox_id_mapper()
            for keyboard_key, bbox_id in enumerate(selected_id):
                self._keyboard_key_to_bbox_id_mapper[keyboard_key] = bbox_id

            print('press key with bbox id you want to select')
            return None

        elif len(selected_id) == 1:
            return selected_id[0]

        return None

    def _turn_on_render_with_id(self):
        self._render_with_id = True

    def _turn_off_render_with_id(self):
        self._render_with_id = False

    def _change_state(self, state: cfg.CanvasState):
        self._state = state

    def _render_bboxes(self, bboxes: List[BBox]):
        self._current_image = self._clear_image.copy()

        # draw bboxes
        for i, bbox in enumerate(bboxes):
            cv2.rectangle(
                self._current_image,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                cfg.CLASS_COLORS[bbox.label],
                cfg.DEFAULT_BBOX_LINE_THICKNESS,
            )

        # draw keyboard numbers to select one of the simultaneously selected bboxes
        for keyboard_number, bbox_id in self._keyboard_key_to_bbox_id_mapper.items():
            bbox = self._bboxes[bbox_id]
            self._current_image = cv2.putText(
                self._current_image,
                str(keyboard_number),
                (bbox.x1, bbox.y1),
                cv2.FONT_HERSHEY_SIMPLEX,
                self._current_image.shape[0] * cfg.TEXTSIZE_IM_WIDTH_RATIO,
                cfg.TEXT_COLOR,
                int(
                    self._current_image.shape[0] * cfg.TEXTTHICKNESS_IM_WIDTH_RATIO
                ),
                cv2.LINE_AA,
            )

        cv2.imshow(cfg.WINDOW_NAME, self._current_image)
