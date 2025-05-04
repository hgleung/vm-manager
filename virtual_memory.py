class VMManager:
    def __init__(self):
        self.PM = [0] * 524288  # Physical memory array
        self.DISK = [[0] * 512 for _ in range(1024)]  # Disk array
        self.segment_table = {}  # Dictionary to store segment table entries
        self.page_tables = {}    # Dictionary to store page tables
        self.used_frames = {0, 1}  # Frames 0,1 reserved for ST (2 frames since each entry is 2 integers)
        self.next_free_frame = 2  # Will be updated after initialization
        self.highest_frame = 1    # Track highest frame number seen
        self.frame_access_count = {}  # For LFU: frame_number -> access count
        self.allocations = {}  # Maps starting physical address to (num_frames, [frame_numbers])

    def get_next_free_frame(self):
        """Find the next available free frame."""
        frame = max(self.next_free_frame, self.highest_frame + 1)
        while frame in self.used_frames:
            frame += 1
        self.used_frames.add(frame)
        self.next_free_frame = frame + 1
        return frame

    def initialize_from_file(self, init_file):
        """Initialize segment and page tables from input file."""
        try:
            with open(init_file, 'r') as file:
                # Read segment table entries (Line 1: s1 z1 f1 s2 z2 f2 ... sn zn fn)
                segment_line = file.readline().strip().split()
                for i in range(0, len(segment_line), 3):
                    s = int(segment_line[i])      # segment number
                    z = int(segment_line[i + 1])  # segment size
                    frame = int(segment_line[i + 2])  # frame/block number
                    
                    # Set segment size in ST: PM[2s] = z
                    self.PM[2 * s] = z
                    # Set PT location in ST: PM[2s+1] = frame
                    self.PM[2 * s + 1] = frame
                    
                    if frame > 0:  # PT is in memory
                        self.used_frames.add(frame)
                        self.highest_frame = max(self.highest_frame, frame)

                # Read page table entries (Line 2: s1 p1 f1 s2 p2 f2 ... sm pm fm)
                page_line = file.readline().strip().split()
                for i in range(0, len(page_line), 3):
                    s = int(page_line[i])      # segment number
                    p = int(page_line[i + 1])  # page number
                    frame = int(page_line[i + 2])  # frame/block number
                    
                    if self.PM[2 * s + 1] > 0:  # If PT is resident
                        # Set page frame in PT: PM[PT_base + p] = frame
                        pt_base = self.PM[2 * s + 1] * 512
                        self.PM[pt_base + p] = frame
                        if frame > 0:  # Page is in memory
                            self.used_frames.add(frame)
                            self.highest_frame = max(self.highest_frame, frame)
                    else:  # PT is on disk
                        # Store in disk: D[|PT_block|][p] = frame
                        disk_block = abs(self.PM[2 * s + 1])
                        self.DISK[disk_block][p] = frame
                        if frame > 0:  # Track highest frame even if on disk
                            self.highest_frame = max(self.highest_frame, frame)

                # Update next_free_frame to be after highest frame seen
                self.next_free_frame = self.highest_frame + 1

        except Exception as e:
            print(f"Error initializing from file: {e}")
            raise

    def access_frame(self, frame_number):
        """Increment access count for a frame (for LFU)."""
        if frame_number not in self.frame_access_count:
            self.frame_access_count[frame_number] = 0
        self.frame_access_count[frame_number] += 1

    def evict_lfu_frame(self):
        """Evict the least-frequently-used frame and return its number."""
        # Exclude reserved frames from eviction
        candidate_frames = self.used_frames - {0, 1}
        if not candidate_frames:
            return None  # No frame to evict
        lfu_frame = min(candidate_frames, key=lambda f: self.frame_access_count.get(f, 0))
        self.used_frames.remove(lfu_frame)
        if lfu_frame in self.frame_access_count:
            del self.frame_access_count[lfu_frame]
        return lfu_frame

    def translate_address(self, va):
        """Translate virtual address to physical address."""
        # Extract s, p, w from VA (each 9 bits)
        w = va & 0x1FF          # Last 9 bits
        p = (va >> 9) & 0x1FF   # Middle 9 bits
        s = (va >> 18) & 0x1FF  # First 9 bits
        pw = va & 0x3FFFF       # Last 18 bits (p and w combined)

        # Check if segment exists and if VA is within segment bounds
        if s * 2 >= len(self.PM) or self.PM[2 * s] == 0:
            return None  # Segment fault
        if pw >= self.PM[2 * s]:
            return None  # Offset beyond segment size

        # Get PT location from ST
        pt_loc = self.PM[2 * s + 1]
        # If PT is not resident (negative frame number)
        if pt_loc < 0:
            pt_loc = self.handle_page_fault(s, None, is_pt=True)
            if pt_loc is None:
                return None
        self.access_frame(pt_loc)  # Access PT frame

        # Get page frame from PT
        page_frame = self.PM[pt_loc * 512 + p]
        # If page is not resident (negative frame number)
        if page_frame < 0:
            page_frame = self.handle_page_fault(s, p, is_pt=False)
            if page_frame is None:
                return None
        self.access_frame(page_frame)  # Access page frame

        # Calculate final physical address
        return page_frame * 512 + w

    def handle_page_fault(self, segment, page, is_pt=False):
        """Handle a page fault for a page table or a page. Returns the frame number used, or None if failed."""
        # Try to get a free frame
        if len(self.used_frames) < 1024:
            frame = self.get_next_free_frame()
        else:
            frame = self.evict_lfu_frame()
            if frame is None:
                return None
        # Simulate loading from disk
        if is_pt:
            # Loading a page table
            pt_disk_block = abs(self.PM[2 * segment + 1])
            # In a real system, copy PT from disk to frame
            self.PM[2 * segment + 1] = frame  # Update ST to point to new PT frame
        else:
            # Loading a page
            pt_loc = self.PM[2 * segment + 1]
            disk_block = abs(self.PM[pt_loc * 512 + page])
            # In a real system, copy page from disk to frame
            self.PM[pt_loc * 512 + page] = frame  # Update PT to point to new page frame
        return frame

    def process_addresses(self, input_file, output_file):
        """Process virtual addresses from input file and write results to output file."""
        with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
            vas = fin.readline().strip().split()
            results = []
            for va in vas:
                pa = self.translate_address(int(va))
                if pa is not None:
                    results.append(str(pa))
                else:
                    results.append("-1")
            fout.write(" ".join(results))

    def malloc(self, size):
        """
        Allocate a block of memory of size words. Returns the starting physical address or -1 if failed.
        
        Note: This malloc implementation only allocates contiguous blocks of physical frames.
        It does NOT support non-contiguous (scattered) frame allocation, unlike a real virtual memory system with paging.
        If sufficient contiguous frames are not available, malloc will fail even if enough total free frames exist.
        This design choice simplifies the allocator but may cause fragmentation and allocation failures under heavy use.
        """
        import math
        FRAME_SIZE = 512
        MAX_FRAMES = 1024
        num_frames = math.ceil(size / FRAME_SIZE)
        attempts = 0
        while attempts <= MAX_FRAMES:
            # Search for a block of num_frames consecutive free frames
            cur_frame = self.next_free_frame
            while cur_frame <= MAX_FRAMES - num_frames:
                block_free = True
                for offset in range(num_frames):
                    if (cur_frame + offset) in self.used_frames:
                        block_free = False
                        break
                if block_free:
                    frame_list = []
                    for offset in range(num_frames):
                        frame_num = cur_frame + offset
                        self.used_frames.add(frame_num)
                        self.highest_frame = max(self.highest_frame, frame_num)
                        frame_list.append(frame_num)
                    next_candidate = cur_frame + num_frames
                    while next_candidate in self.used_frames and next_candidate < MAX_FRAMES:
                        next_candidate += 1
                    self.next_free_frame = next_candidate
                    start_addr = cur_frame * FRAME_SIZE
                    self.allocations[start_addr] = (num_frames, frame_list)
                    return start_addr
                cur_frame += 1
            # If we reach here, no contiguous block is available; evict one LFU frame and try again
            lfu_frame = self.evict_lfu_frame()
            if lfu_frame is None:
                break
            # Remove lfu_frame from any allocation it belonged to
            to_remove = []
            for addr, (nframes, frames) in self.allocations.items():
                if lfu_frame in frames:
                    frames.remove(lfu_frame)
                    if not frames:
                        to_remove.append(addr)
                    else:
                        self.allocations[addr] = (len(frames), frames)
            for addr in to_remove:
                del self.allocations[addr]
            attempts += 1
        return -1

    def free(self, address) -> bool:
        """Free the memory block starting at the given physical address."""
        if address not in self.allocations:
            return False  # Invalid free
        _, frame_list = self.allocations[address]
        for frame in frame_list:
            if frame in self.used_frames:
                self.used_frames.remove(frame)
            if frame in self.frame_access_count:
                del self.frame_access_count[frame]
        del self.allocations[address]
        
        return True

    def realloc(self, address, new_size) -> int:
        """Resize the memory block at address to new_size words. Returns new address or -1 if failed."""
        if address not in self.allocations:
            return -1  # Invalid realloc
        import math
        FRAME_SIZE = 512
        old_num_frames, old_frames = self.allocations[address]
        new_num_frames = math.ceil(new_size / FRAME_SIZE)
        # If new size fits in the same block, do nothing
        if new_num_frames == old_num_frames:
            return address
        # If shrinking, free extra frames
        if new_num_frames < old_num_frames:
            frames_to_free = old_frames[new_num_frames:]
            for frame in frames_to_free:
                if frame in self.used_frames:
                    self.used_frames.remove(frame)
                if frame in self.frame_access_count:
                    del self.frame_access_count[frame]
            self.allocations[address] = (new_num_frames, old_frames[:new_num_frames])
            return address
        # If growing, try to allocate a new block and copy
        new_addr = self.malloc(new_size)
        if new_addr == -1:
            return -1  # Failed to allocate new block
        # Simulate copying data from old block to new block (not implemented)
        self.free(address)
        return new_addr

def main():
    vm = VMManager()
    vm.initialize_from_file("init-dp.txt")
    vm.process_addresses("input-dp.txt", "output.txt")

if __name__ == "__main__":
    main()
