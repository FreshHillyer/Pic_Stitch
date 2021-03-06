import numpy as np
import cv2
from Optimize.resize import resize
from Optimize.cropImg import handleImage
from matplotlib import pyplot as plt
import os

def pic_sti(str_in1,str_in2,str_out):
    
    resize(str_in1,str_in2)
    
    top, bot, left, right = 100, 100, 0, 500

    img_1 = cv2.imread(str_in1)
    img_2 = cv2.imread(str_in2)

    # padding for edg of picture
    Img_1 = cv2.copyMakeBorder(img_1, top, bot, left, right, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    Img_2 = cv2.copyMakeBorder(img_2, top, bot, left, right, cv2.BORDER_CONSTANT, value=(0, 0, 0))

    # img1_gray = cv2.cvtColor(Img_1, cv2.COLOR_BGR2GRAY)
    # img2_gray = cv2.cvtColor(Img_2, cv2.COLOR_BGR2GRAY)

    # Initiate SIFT detector
    sift = cv2.xfeatures2d_SIFT().create()

    # find keypoints and descriptors with SIFT
    kp_1, des_1 = sift.detectAndCompute(img_1, None)
    kp_2, des_2 = sift.detectAndCompute(img_2, None)

    # Set FLANN parameters
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_1, des_2, k=2)

    # create a mask for drawing only good matches
    matchesMask = [[0, 0] for i in range(len(matches))]

    good = []
    pts1 = []
    pts2 = []

    # store all the good matches as per Lowe's ratio test.
    DISTANCE_LIMIT = 0.7
    
    for i, (m, n) in enumerate(matches):
        if m.distance < DISTANCE_LIMIT * n.distance:
            good.append(m)
            pts2.append(kp_2[m.trainIdx].pt)
            pts1.append(kp_1[m.queryIdx].pt)
            matchesMask[i] = [1, 0]

    draw_params = dict(matchColor=(0, 255, 0),
                       singlePointColor=(255, 0, 0),
                       matchesMask=matchesMask,
                       flags=0)
    
    img3 = cv2.drawMatchesKnn(img_1, kp_1, img_2, kp_2, matches, None, **draw_params)
    img3 = cv2.cvtColor(img3, cv2.COLOR_BGR2RGB)
    plt.imshow(img3, ), plt.show()
    target_path = os.path.abspath("..") + '/test/process/process.jpg'
    plt.imsave(target_path, img3)

    rows, cols = Img_1.shape[:2]
    MIN_MATCH_COUNT = 10
    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp_1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        warpImg = cv2.warpPerspective(Img_2, np.array(M), (Img_2.shape[1], Img_2.shape[0]),
                                     flags=cv2.WARP_INVERSE_MAP)

        for col in range(0, cols):
            if Img_1[:, col].any() and warpImg[:, col].any():
                left = col
                break
        for col in range(cols - 1, 0, -1):
            if Img_1[:, col].any() and warpImg[:, col].any():
                right = col
                break

        res = np.zeros([rows, cols, 3], np.uint8)
        for row in range(0, rows):
            for col in range(0, cols):
                if not Img_1[row, col].any():
                    res[row, col] = warpImg[row, col]
                elif not warpImg[row, col].any():
                    res[row, col] = Img_1[row, col]
                else:
                    srcImgLen = float(abs(col - left))
                    testImgLen = float(abs(col - right))
                    alpha = srcImgLen / (srcImgLen + testImgLen)
                    res[row, col] = np.clip(Img_1[row, col] * (1 - alpha) + warpImg[row, col] * alpha, 0, 255)

        # opencv is bgr, matplotlib is rgb
        res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        plt.figure()
        # optimizations in twe methods
        try:
            res_1 = handleImage(res)
            plt.imshow(res_1)
            target_path = os.path.abspath("..") + '/test/res_Pic/' + str_out
            plt.imsave(target_path, res_1)
        except:
            plt.imshow(res)
            target_path = os.path.abspath("..") + '/test/res_Pic/' + str_out
            plt.imsave(target_path, res)
        plt.show()

    #print(res)
        # plt.figure()
        # plt.imshow(res_1)
        # plt.imshow(res_2)
        # plt.show()
        # target_path_1 = os.path.abspath("..")+'/test/res_Pic/1_'+str_out
        # target_path_2 = os.path.abspath("..") + '/test/res_Pic/2_' + str_out
        # plt.imsave(target_path_1,res_1)
        # plt.imsave(target_path_2, res_2)
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    # # just key points in good set
    # draw_params = dict(matchColor=(0, 255, 0),
    #                    singlePointColor=None,
    #                    matchesMask=matchesMask,
    #                    flags=2)
    # img3 = cv2.drawMatches(img_1, kp_1, img_2, kp_2, good, None, **draw_params)
    # plt.imshow(img3, cmap='gray')
    # plt.show()
    # plt.imsave('process/process.jpg', changeSize.change_size(img3))
