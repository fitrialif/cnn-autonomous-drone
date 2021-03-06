#!/usr/bin/env python

class AnnotateBase(object):
    def __init__(self, num_actions=2):
        super(AnnotateBase, self).__init__()
        self.image_data = None
        self.num_images = 0
        self.width = 0
        self.height = 0
        self.scale = 4
        self.labels = None
        self.data = None
        self.num_annotated = 0
        self.chans = 3
        # Should be careful about setting num_actions here
        self.num_actions = num_actions

if __name__ == '__main__':
    print('Base class for state used by Annotator')
