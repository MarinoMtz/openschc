#---------------------------------------------------------------------------

from base_import import *

import schcmsg
from math import floor

#---------------------------------------------------------------------------

class TileList():

    # XXX it is almost about the sender side, should be moved into schcsend.py.
    # XXX may it be used in NO-ACK ?
    def __init__(self, rule, packet_bbuf):
        self.rule = rule
        self.t_size = rule["tileSize"]
        t_init_num = schcmsg.get_MAX_WIND_FCN(rule)
        self.all_tiles = []
        w_num = 0
        t_num = t_init_num
        # make tiles
        # XXX for now, the packet bitbuffer is going to be divided
        # into the tiles, which are a set of bit buffers too.
        # logically, it doesn't need when tileSize is well utilized.
        bbuf = packet_bbuf.copy()
        num_full_size_tiles = floor(bbuf.count_added_bits()/self.t_size)
        last_tile_size = bbuf.count_added_bits() - (self.t_size *
                                                  num_full_size_tiles)
        assert last_tile_size >= 0
        tiles = [ bbuf.get_bits_as_buffer(self.t_size)
                 for _ in range(num_full_size_tiles) ]
        if last_tile_size > 0:
            tiles.append(bbuf.get_bits_as_buffer(last_tile_size))
        # make a all_tiles
        for t in tiles:
            tile_obj = {
                    "w-num": w_num,
                    "t-num": t_num,
                    "tile": t,
                    "sent": False,
                    "ready_to_be_sent": False,
                }
            self.all_tiles.append(tile_obj)
            if t_num == 0:
                t_num = t_init_num
                w_num += 1
            else:
                t_num -= 1
        print("DEBUG: all_tiles:")
        for i in self.all_tiles:
            print("DEBUG:  ", i)

    def get_tiles(self, mtu_size):
        '''
        return the tiles containing the contiguous tiles fitting in mtu_size.
        And, remaiing nb_tiles to be sent in all_tiles.
        '''
        remaining_size = mtu_size - schcmsg.get_sender_header_size(self.rule)
        max_tiles = remaining_size // self.t_size
        tiles = []
        t_prev = None
        for i in range(len(self.all_tiles)):
            t = self.all_tiles[i]
            '''
            if t_prev and t_prev["t-num"] + 1 < t["t-num"]:
                break
            '''
            if t["sent"] == False:
                tiles.append(t)
                assert t["ready_to_be_sent"] == False
                t["ready_to_be_sent"] = True
                t_prev = t
            if len(tiles) == max_tiles:
                break
        if len(tiles) == 0:
            return None, 0, remaining_size
        # return tiles and the remaining bits
        nb_remaining_tiles = len(
                [ _ for _ in self.all_tiles if _["ready_to_be_sent"] == False ])
        remaining_size -= self.get_tile_size(tiles)
        return tiles, nb_remaining_tiles, remaining_size

    def get_all_tiles(self):
        return self.all_tiles

    def update_sent_flag(self):
        for t in self.all_tiles:
            if t["ready_to_be_sent"] == True:
                t["sent"] = True

    @staticmethod
    def get_tile_size(tiles):
        size = 0
        for i in tiles:
            size += i["tile"].count_added_bits()
        return size

    @staticmethod
    def concat(tiles):
        bbuf = BitBuffer()
        for t in tiles:
            bbuf += t["tile"]
        return bbuf

#---------------------------------------------------------------------------
