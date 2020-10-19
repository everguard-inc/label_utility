import cv2
import os
import json
IMAGE_FOLDER="/Users/serhii/Downloads/datasets/vest_helmet_final/images/"
JSON_PATH='/Users/serhii/Downloads/full_train_new_without_height_width.json'
WRITE_FOLDER = "/Users/serhii/Downloads/datasets/vest_helmet_final/testing_json/"


class Color:
    Red = (0, 0, 255)
    Lime = (0, 255, 0)
    Blue = (255, 0, 0)
    LightBlue = (170, 178, 32)
    Yellow = (0, 255, 255)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Orange = (0, 140, 255)
    Olive = (35, 142, 107)
    Green = (0, 128, 0)
    Purple = (211, 0, 148)
    Pink = (180, 20, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Gray = (192, 192, 192)
    Brown = (19, 69, 139)



write_ann_dir = os.path.join(WRITE_FOLDER, "annotations")
write_img_dir = os.path.join(WRITE_FOLDER, "images")

if not os.path.exists(write_ann_dir):
    os.makedirs(write_ann_dir)
if not os.path.exists(write_img_dir):
    os.makedirs(write_img_dir)

with open(JSON_PATH) as f:
    d = json.load(f)

images=[]
images_dict={}
for im in d["images"]:
        images.append(im["file_name"])
        images_dict[im["id"]]=im["file_name"]

for i in d["annotations"]:
    i["file_name"]=images_dict[i["image_id"]]

def draw_bboxes(boxes,img):
    if len(boxes)>0:
        for i in boxes:
            if int(i[4])==0:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Red, 4)
            if int(i[4])==1:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Yellow, 4)
            if int(i[4])==2:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Blue, 4)
            if int(i[4])==3:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Green, 4)
            if int(i[4])==4:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Black, 4)
            if int(i[4])==5:
                cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), Color.Purple, 4)

c=0
for i in range(len(images)):
    drawing=False
    deleting=False
    invisible=False
    if i==0:
        pop=0
    if pop==2:
        break
    pop=0
    print(images[c])
    final_boxes=None
    path=IMAGE_FOLDER+images[c]
    img=cv2.imread(path)
    boxes=[]
    for box_js in d["annotations"]:
        if box_js["file_name"]==images[c]:
            box_new=box_js["bbox"].copy()
            box_new.append(box_js["category_id"])
            boxes.append(box_new)
    #with open(IMAGE_FOLDER+"annotations/"+images[c].split(".")[0]+".txt", "r") as fp:
        #boxes = json.load(fp)
    draw_bboxes(boxes,img)
    cv2.imshow('image',img)
    draw_mouse = False
    mode = True
    x1,y1 = -1,-1
    while pop<1:
        def onMouse(event, x, y, flags, param):
            global x1,y1,draw_mouse,mode,drawing,deleting,invisible
            if deleting==True:
                selected_boxes=[]
                try:
                    final_boxes
                except NameError:
                    final_boxes=boxes
                img=cv2.imread(path)
                draw_bboxes(final_boxes,img)
                if event == cv2.EVENT_LBUTTONDOWN:
                    point=x,y
                    numbers=[]
                    for c in range(len(final_boxes)):
                        if final_boxes[c][0]<x<final_boxes[c][2]+final_boxes[c][0] and final_boxes[c][1]<y<final_boxes[c][3]+final_boxes[c][1]:
                            selected_boxes.append(final_boxes[c])
                            numbers.append(c)
                    if len(selected_boxes)>1:
                        img=cv2.imread(path)
                        for b,i in enumerate(selected_boxes):
                            img=cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), (255, 0, 0) , 4)
                            img=cv2.putText(img, str(b), (int(i[0]),int(i[1])), cv2.FONT_HERSHEY_SIMPLEX , int(img.shape[0]/300), (0,50,0), int(img.shape[0]/100), cv2.LINE_AA)
                        cv2.imshow('image',img)
                        cv2.waitKey()
                        num = input("Which one you want to delete? 1,2 etc.\n")
                        print(final_boxes)
                        del final_boxes[numbers[int(int(num))]]
                    else:
                        del final_boxes[numbers[0]]
                    deleting=False
                    
            if drawing==True:
                try:
                    final_boxes
                except NameError:
                    final_boxes=boxes
                img=cv2.imread(path)
                draw_bboxes(final_boxes,img)
                if event == cv2.EVENT_LBUTTONDOWN:
                    draw_mouse=True
                    x1,y1 = x,y
                elif event == cv2.EVENT_MOUSEMOVE:
                    if draw_mouse == True:
                        if mode == True:
                            cv2.rectangle(img,(x1,y1),(x,y),(0,255,0),3)
                        cv2.imshow('image',img)
                elif event == cv2.EVENT_LBUTTONUP:
                    draw_mouse = False
                    if mode == True:
                        cv2.rectangle(img,(x1,y1),(x,y),(0,255,0),2)
                    cv2.imshow('image',img)
                    cv2.waitKey()
                    nums = input("What class? 0 - person,1 - with_helmet, 2 - with_vest, 3 - with_vest_and_helmet, 4 - invisible_without_vest, 5 - invisible_with_vest\n")
                    final_x1=min(x,x1)
                    final_x2=max(x,x1)

                    final_y1=min(y,y1)
                    final_y2=max(y,y1)
                    
                    final_boxes.append([final_x1,final_y1,final_x2-final_x1,final_y2-final_y1,nums])
                    drawing=False
                
            if invisible==True:
                selected_boxes=[]
                try:
                    final_boxes
                except NameError:
                    final_boxes=boxes
                if event == cv2.EVENT_LBUTTONDOWN:
                    point=x,y
                    numbers=[]
                    for c in range(len(final_boxes)):
                        if final_boxes[c][0]<x<final_boxes[c][2]+final_boxes[c][0] and final_boxes[c][1]<y<final_boxes[c][3]+final_boxes[c][1]:
                            selected_boxes.append(final_boxes[c])
                            numbers.append(c)
                    if len(selected_boxes)>1:
                        img=cv2.imread(path)
                        for b,i in enumerate(selected_boxes):
                            img=cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), (255, 0, 0) , 4)
                            img=cv2.putText(img, str(b), (int(i[0]),int(i[1])), cv2.FONT_HERSHEY_SIMPLEX , int(img.shape[0]/300), (0,50,0), int(img.shape[0]/100), cv2.LINE_AA)
                        cv2.imshow('image',img)
                        cv2.waitKey()
                        num = input("Which one are invisible?\n")
                        if final_boxes[c][4]==2 or final_boxes[c][4]==3:
                                final_boxes[numbers[int(num)]][4]=5
                        else:
                            final_boxes[numbers[int(num)]][4]=4

                    else:
                        for c in range(len(final_boxes)):
                            if final_boxes[c][0]<x<final_boxes[c][2]+final_boxes[c][0] and final_boxes[c][1]<y<final_boxes[c][3]+final_boxes[c][1]:
                                if final_boxes[c][4]==2 or final_boxes[c][4]==3:
                                    final_boxes[c][4]=5
                                else:
                                    final_boxes[c][4]=4
                            
                if event == cv2.EVENT_RBUTTONDOWN:
                    point=x,y
                    numbers=[]
                    for c in range(len(final_boxes)):
                        if final_boxes[c][0]<x<final_boxes[c][2] and final_boxes[c][1]<y<final_boxes[c][3]:
                            selected_boxes.append(final_boxes[c])
                            numbers.append(c)
                    if len(selected_boxes)>1:
                        img=cv2.imread(path)
                        cv2.imshow('image',img)
                        for b,i in enumerate(selected_boxes):
                            img=cv2.rectangle(img, (int(i[0]),int(i[1]),int(i[2]),int(i[3])), (255, 0, 0) , 4)
                            img=cv2.putText(img, str(b), (int(i[0]),int(i[1])), cv2.FONT_HERSHEY_SIMPLEX , int(img.shape[0]/300), (0,50,0), int(img.shape[0]/100), cv2.LINE_AA)
                        cv2.imshow('image',img)
                        cv2.waitKey()
                        num = input("Which one are without vest?")
                        if final_boxes[numbers[int(num)]][4]>1:
                                    final_boxes[numbers[int(num)]][4]=-2

                    else:
                        for c in range(len(final_boxes)):
                            if final_boxes[c][0]<x<final_boxes[c][2] and final_boxes[c][1]<y<final_boxes[c][3]:
                                if final_boxes[c][4]>1:
                                    final_boxes[c][4]-=2
        
                    invisible=False
        cv2.namedWindow('image',cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback('image', onMouse)
        k=cv2.waitKey()
        if k==ord("l"):
            if final_boxes is None: 
                final_boxes=boxes
            for l,i in enumerate(final_boxes):
                final_boxes[l][4]=final_boxes[l][4]+2
            cv2.waitKey()
        for cc in boxes:
            cc[4]=int(cc[4])
        if k==ord("w"):
            drawing=True
        if k==ord("d"):
            deleting=True
        if k==ord("i"):
            invisible=True  
        if k==ord("f"):
            img=cv2.imread(path)
            if final_boxes is None:
                final_boxes=boxes
            print(final_boxes)
            draw_bboxes(final_boxes,img)
            cv2.imshow('image',img)
        if k==ord("n"):
            c=c+1
            pop=pop+1
        if k==ord("r"):
            pop=pop+1
        if k==ord("y"):
            img=cv2.imread(path)
            img_write=WRITE_FOLDER+"images/"+images[c].split(".")[0]+".jpg"
            cv2.imwrite(img_write, img)
            with open(WRITE_FOLDER+"annotations/"+images[c].split(".")[0]+".txt", "w") as output:
                json.dump(boxes, output)
            c=c+1
            pop=pop+1
        elif k==ord("q"):
            pop=2
            cv2.destroyAllWindows()
            break