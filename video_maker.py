import os.path
import glob
import os

import imageio
import fire


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1,
                     length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def write_video(video, images_folder, images_pattern="*.jpg", fps=30):
    """Write a timelapse video using the photos of a folder"""
    images_glob = os.path.join(images_folder, images_pattern)
    filenames = sorted(glob.glob(images_glob))
    images_cnt = len(filenames)
    print("Found %d images" % (images_cnt))
    print("At %d fps the resulting video will be %f seconds long" %
          (fps, images_cnt/fps))
    with imageio.get_writer(video, mode='I', fps=fps) as writer:
        print("Writing video: %s" % (os.path.basename(video)))
        for i, filename in enumerate(filenames):
            printProgressBar(i+1, images_cnt, prefix='Progress:',
                             suffix='Complete', length=50)
            image = imageio.imread(filename)
            writer.append_data(image)


def write_all(video_folder, source_folder, video_extension, images_pattern="*.jpg", fps=30):
    """Write a timelapse video for each folder"""
    for cur in os.listdir(source_folder):
        path = os.path.join(source_folder, cur)
        if os.path.isdir(path):
            target_filepath = os.path.join(
                video_folder, cur + '.' + video_extension)
            write_video(target_filepath, path, images_pattern, fps)


def main():
    fire.Fire({
        'one': write_video,
        'all': write_all,
    })


if __name__ == '__main__':
    main()
