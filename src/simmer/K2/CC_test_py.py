import numpy as np
import scipy as sp
from astropy.stats import SigmaClip
from astropy.stats import sigma_clipped_stats
from astropy.io import fits
import photutils
import math



def contrast_curve_3(data,center=None,remove_hot=False,background_method='astropy',radius_size=1):
    
    star_data=data.copy()
    
    x, y = np.indices((star_data.shape))
    
    if not center:
        center = np.array([(x.max()-x.min())/2.0, (y.max()-y.min())/2.0])
        
    center_x1,center_x2 = int(center[0]-.5) ,int(center[0]+.5)
    center_y1,center_y2 = int(center[1]-.5),int(center[1]+.5)
    center_points = (star_data[center_x1,center_y1],star_data[center_x1,center_y2],star_data[center_x2,center_y1],star_data[center_x2,center_y2])
    center_val = np.mean(center_points) + 5*np.std(center_points)
    radii =  np.sqrt((x - center[0])**2 + (y - center[1])**2)
    radii = radii.astype(np.int)

    #Method 1 for background - Everything outside center (bad for companions)
    if background_method=='outside':
        non_center = []
        for i in range(len(star_data)):
            for j in range(len(star_data[i])):
                if i<265 or i>335 or j<265 or j>335:
                    non_center.append(star_data[i,j])
        background_mean = np.mean(non_center)
        background_std = np.std(non_center)
    
    #Method 2 for background - 4 Box method (remove a box if it is wonky/high)
    if background_method=='boxes':
        box1,box2,box3,box4=star_data[100:200,100:200],star_data[100:200,400:500],star_data[400:500,100:200],star_data[400:500,400:500]
        mean_box1,mean_box2,mean_box3,mean_box4 = np.mean(box1),np.mean(box2),np.mean(box3),np.mean(box4)
        std_box1,std_box2,std_box3,std_box4 = np.std(box1),np.std(box2),np.std(box3),np.std(box4)
        
        mean_boxes = []
        std_boxes = []
        if mean_box1 < (10*np.mean([std_box2,std_box3,std_box4]) + np.mean([mean_box2,mean_box3,mean_box4])):
            mean_boxes.append(mean_box1)
            std_boxes.append(std_box1)
        if mean_box2 < (10*np.mean([std_box1,std_box3,std_box4]) + np.mean([mean_box1,mean_box3,mean_box4])):
            mean_boxes.append(mean_box2)
            std_boxes.append(std_box2)
        if mean_box3 < (10*np.mean([std_box1,std_box2,std_box4]) + np.mean([mean_box1,mean_box2,mean_box4])):
            mean_boxes.append(mean_box3)
            std_boxes.append(std_box3)
        if mean_box4 < (10*np.mean([std_box2,std_box3,std_box1]) + np.mean([mean_box2,mean_box3,mean_box1])):
            mean_boxes.append(mean_box4)
            std_boxes.append(std_box4)
        background_mean = np.mean(mean_boxes)
        background_std = np.mean(std_boxes)
        print('box means:',mean_boxes,'box stds:',std_boxes)
    #Method 3 for background - simple astropy
    if background_method=='astropy':
        background_mean,background_median,background_std = sigma_clipped_stats(star_data,sigma=5)
    
    
    
    number_of_a = radii.max()/radius_size
    if radius_size>1:
        for i in range(int(number_of_a)+2):
            if i==0:
                continue
            radii[(radii>0) & (radii<=i*radius_size) & (radii>radius_size*(i-1))] =(i)
            
    
    radii_arc_length = []
    bins=[]
    for i in range(radii.max()+1):
        radii_arc_length.append(i*0.033*radius_size + 0.033)
        bins.append([])
    radii_arc_length = np.array(radii_arc_length)
    lim_arc_length=radii_arc_length
    lim_arc_length= radii_arc_length[radii_arc_length<8]
    
    for i in range(len(radii)):
        for j in range(len(radii[i])):
            bins[radii[i,j]].append(np.array([i,j]))
    bins = bins[:len(lim_arc_length)]
    
    #Remove hot pixel (only works for non binary atm)
    if remove_hot==True:
        print('looking for hots')
        for i in range(600):
            for j in range(600):
                if (i<265 or i>335 or j<265 or j>335) & (star_data[i,j]>(background_mean+10*background_std)):
                    print('hot pixel alert:',star_data[i,j],'at',[i,j],'arc_length',)
                    star_data[i,j] = np.mean([star_data[i+1,j],star_data[i-1,j],star_data[i,j+1],star_data[i,j-1]])
    
    radii_bin_vals = []
    for i in range(len(bins)):
        radii_bin = []
        for j in range(len(bins[i])):
            radii_bin.append(star_data[bins[i][j][0],bins[i][j][1]])
        radii_bin_vals.append(radii_bin)
    radii_deltas = []
    
    
    

    #print(background_mean,background_std)
    
    
    rbv_count = 0
    for i in radii_bin_vals:
        rbv_count+=1
        try:
            radii_deltas.append(-2.5 * math.log((np.mean(i) + 5*np.std(i))/center_val,10))
        except:
            print('mean less than/equal to zero in bin',rbv_count,'val of',np.mean(i))
            radii_deltas.append(np.NaN)
    radii_deltas=np.array(radii_deltas)
    return np.array([lim_arc_length,radii_deltas])

