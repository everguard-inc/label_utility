# label_utility

#### Run
```
python3 main.py --input_coco <input_coco_path> \
--output_folder <output_folder_path> \
--images <images_folder_path>
```

#### Control keys
| Key | Action | 
| --- | --- |
| Y  | Save and open next image | 
| N  | Skip image | 
| R  | Undo | 
| W  | Draw bbox |
| D  | Delete mode |
| I  | Renaming mode | 
| Q  | Quit | 


#### Classes keys
| Key | Class | 
| --- | --- |
| 0  | person | 
| 1  | with_helmet | 
| 2  | with_vest | 
| 3  | with_vest_and_helmet | 
| 4  | invisible_without_vest |
| 5  | invisible_with_vest |


#### Create bbox
1. Select a class by pressing the class hotkey or leave the class you selected earlier. The class name will be displayed on the command line
2. Press W
3. Draw ROI. You can draw it several times until it is positioned as you want. Each time the previously drawn bbox will be removed.
4. When done - press space

#### Rename bbox
1. Press I
2. Press the hotkey of the class you want
3. Click on bbox you want to rename

#### Delete bbox
1. Press D
2. Left click on bbox



