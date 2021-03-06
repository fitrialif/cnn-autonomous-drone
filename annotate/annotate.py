#!/usr/bin/env python2
#
from __future__ import print_function
from io import BytesIO
import numpy as np
import argparse, sys, os, pdb

sys.path.append(os.path.abspath('..'))
from shared.action import Action
from shared.imagewindow import ImageWindow
from shared.annotate_base import AnnotateBase


class Annotator(AnnotateBase):
    def __init__(self, num_actions=4):
        super(Annotator, self).__init__(num_actions=num_actions)

    def _load_data(self, file):
        npz = np.load(file)
        self.image_data = npz['image_data']
        self.num_images = self.image_data.size
        (self.width, self.height) = Image.open(BytesIO(self.image_data[0])).size

        assert self.width==856 and self.height==480, "Unexpected image dimensions (%d, %d)" % (self.width, self.height)

    def annotate(self, file):
        self._load_data(file)
        w = self.width
        h = self.height
        s = self.scale
        c = self.chans
        size = w*h/s/s*c
        iw = ImageWindow(w/2, h/2)
        self.labels = np.empty(self.num_images, dtype='byte')
        self.data = np.empty((self.num_images, size), dtype='byte')
        keep = np.ones(self.num_images)

        # Check that our incoming image size is as expected...
        image = Image.open(BytesIO(self.image_data[0]))
        resized = image.resize((w/s, h/s), resample=Image.LANCZOS)
        hsv = resized.convert('HSV')
        assert size == np.fromstring(hsv.tobytes(), dtype='byte').size, "Unexpected image size!"

        i = 0
        while i < self.num_images:
            image = Image.open(BytesIO(self.image_data[i]))\
                         .crop((w/s, h/s, (s-1)*w/s, (s-1)*h/s))
            resized = image.resize((w/s, h/s), resample=Image.LANCZOS)
            hsv = resized.convert('HSV')

            iw.show_image(image)
            iw.force_focus()

            if keep[i]==1:
                print('Image {} / {}: '.format(i, self.num_images), end='')
            else:
                print('Image {} / {} (KILLED): '.format(i, self.num_images), end='')
            sys.stdout.flush()

            iw.wait()

            key = iw.get_key()

            if key=='Escape':
                print('(QUIT)')
                break
            elif key=='BackSpace':
                if i > 0:
                    i -= 1
                print('(BACK)')
                continue
            elif key=='k':
                print('(KILLED)')
                keep[i] = 0
                label = Action.SCAN
            elif key=='r':
                print('(RESTORED)')
                keep[i] = 1
                if i > 0:
                    i -= 1
                continue
            elif key=='space':
                label = Action.SCAN
            elif key=='Return':
                label = Action.TARGET
            elif self.num_actions > 2 and key=='Left':
                label = Action.TARGET_LEFT
            elif self.num_actions > 2 and key=='Right':
                label = Action.TARGET_RIGHT
            elif self.num_actions > 4 and key=='Up':
                label = Action.TARGET_UP
            elif self.num_actions > 4 and key=='Down':
                label = Action.TARGET_DOWN
            else:
                label = Action.SCAN

            self.labels[i] = label
            self.data[i] = np.fromstring(hsv.tobytes(), dtype='byte')
            print(Action.name(label))
            i += 1

        iw.close()
        self.num_annotated = i
        self.labels = self.labels[:i]
        self.data = self.data[:i]
        self.labels = self.labels[keep[:i]==1]
        self.data = self.data[keep[:i]==1]
        self.num_annotated = len(self.labels)


    def save(self, outfile):
        n = self.num_annotated
        np.savez(outfile, data=self.data[:n], labels=self.labels[:n])


    def reannotate(self, bagfile, npzfile_in):
        # self._load_bag_data(bagfile) # self.num_images set here
        w = self.width
        h = self.height
        s = self.scale
        c = self.chans
        size = w*h/s/s*c
        iw = ImageWindow(w/2, h/2)
        edit = False


        npz = np.load(npzfile_in)
        labels = self.labels = npz['labels']
        n = self.num_annotated = labels.shape[0]

        if self.num_images != self.num_annotated:
            print('Warning: bag and npz file lengths differ ({} vs {})'.format(self.num_images, self.num_annotated))

        data = self.data = np.empty((self.num_annotated, size), dtype='byte')

        # Check that our incoming image size is as expected...
        image = Image.open(BytesIO(self.image_data[0]))
        resized = image.resize((w/s, h/s), resample=Image.LANCZOS)
        hsv = resized.convert('HSV')
        assert size == np.fromstring(hsv.tobytes(), dtype='byte').size, "Unexpected image size!"

        i = 0
        while i < self.num_annotated:
            image = Image.open(BytesIO(self.image_data[i]))\
                         .crop((w/s, h/s, (s-1)*w/s, (s-1)*h/s))
            resized = image.resize((w/s, h/s), resample=Image.LANCZOS)
            hsv = resized.convert('HSV')
            iw.show_image(image)
            iw.force_focus()

            if edit:
                print('Image {} / {} ({}): '.format(i, self.num_annotated, Action.name(labels[i])), end='')
                sys.stdout.flush()
            else:
                print('Image {} / {}: {}'.format(i, n, Action.name(labels[i])))
                if labels[i] >= self.num_actions:
                    print ('>>> CHANGING TO {}'.format(Action.name(Action.SCAN)))
            iw.wait()

            key = iw.get_key()

            if key=='Escape':
                print('(QUIT)')
                break
            elif key=='BackSpace':
                if i > 0:
                    i -= 1
                print('(BACK)')
                continue
            elif key=='e':
                if edit:
                    edit = False
                    print('(EDIT OFF)')
                else:
                    edit = True
                    print('(EDIT ON)')
                continue
            elif not edit:
                if labels[i] >= self.num_actions:
                    label = Action.SCAN
                else:
                    label = self.labels[i]
            elif key=='space':
                label = Action.SCAN
            elif key=='Return':
                label = Action.TARGET
            elif self.num_actions > 2 and key=='Left':
                label = Action.TARGET_LEFT
            elif self.num_actions > 2 and key=='Right':
                label = Action.TARGET_RIGHT
            elif self.num_actions > 4 and key=='Up':
                label = Action.TARGET_UP
            elif self.num_actions > 4 and key=='Down':
                label = Action.TARGET_DOWN
            else:
                label = Action.SCAN

            self.labels[i] = label
            self.data[i] = np.fromstring(hsv.tobytes(), dtype='byte')
            if edit:
                print(Action.name(label))
            i += 1

        iw.close()
        self.num_annotated = i

def get_args():
    parser = argparse.ArgumentParser(description='Annotate drone flight images with action commands for supervised learning. NOTE: Python 2 required.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', metavar='<npzfile_in>', help='npz file with image data to analyze')
    parser.add_argument('outfile', metavar='<npzfile_out>', help='npz file for writing results')
    parser.add_argument('--reannotate', metavar='<npzfile_in>', help='npz file to reannotate')

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()

    a = Annotator(num_actions=2)

    if args.reannotate:
        a.reannotate(args.infile, args.reannotate)
        a.save(args.outfile)
    else:
        a.annotate(args.infile)
        a.save(args.outfile)
