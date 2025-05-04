# Virtual Memory Manager for UC Irvine CS 143B

**Author:** Harry Leung

This project implements a virtual memory manager that simulates the translation of virtual addresses to physical addresses using a two-level paging system, including realistic memory management features such as page fault handling, LFU (Least Frequently Used) page replacement, and dynamic memory allocation (malloc, free, realloc).

## Implementation Overview

The core of the project is implemented in `virtual_memory.py`, which defines a `VMManager` class responsible for managing the segment table, page tables, physical memory, and disk simulation. The program reads initialization and address input files, processes virtual address translations, and writes the results to `output.txt`.

### Data Structures
- **Physical Memory (PM):** Simulated as a large array (`self.PM`) of 524,288 integers, representing 1024 frames of 512 words each.
- **Disk (DISK):** Simulated as a 2D array (`self.DISK`) with 1024 blocks, each containing 512 words, used to hold non-resident page tables and pages.
- **Segment Table:** Stored in the first part of `PM`. Each segment has two entries: segment size and the frame/block number of its page table (positive for resident in memory, negative for on disk).
- **Page Tables:** Each page table is allocated to a frame in `PM` or a block in `DISK`.
- **Used Frames:** A set to track which frames are currently allocated to avoid collisions.
- **Frame Access Count:** Tracks how often each frame is accessed, enabling LFU page replacement.
- **Allocations:** Tracks memory allocations for dynamic memory management (malloc, free, realloc).

### Initialization (`initialize_from_file`)
- Reads segment table and page table entries from `init-dp.txt`.
- Segment table entries specify segment number, size, and page table location.
- Page table entries specify segment, page, and frame/block for each page.
- Populates `PM` and `DISK` accordingly, marking frames as used and updating the highest frame number seen.

### Address Translation and Page Fault Handling (`translate_address`, `handle_page_fault`)
- Virtual addresses are split into segment, page, and offset fields.
- Address translation consults the segment and page tables, and may trigger a page fault if a required page or page table is not resident in memory.
- On a page fault, a free frame is allocated if available; otherwise, the LFU (Least Frequently Used) frame is evicted and reused.
- The relevant page or page table is then loaded (simulated) into memory, and tables are updated accordingly.

### Dynamic Memory Management (`malloc`, `free`, `realloc`)
- **malloc:** Allocates a contiguous block of physical memory (in words). If a contiguous block is not available, it uses LFU eviction to free frames and retries. If still unsuccessful, malloc fails. **Design Note:** This malloc does NOT allocate non-contiguous frames, unlike a real paging system. Fragmentation can prevent allocations even if enough total free frames exist.
- **free:** Releases all frames associated with a given allocation address.
- **realloc:** Resizes an allocation (shrinks in place, or allocates a new block and frees the old one).

### LFU Page Replacement
- The VMManager tracks access counts for each frame and uses LFU to evict the least-used frame when memory is full (for both page faults and malloc).

### Processing Input Addresses (`process_addresses`)
- Reads a list of virtual addresses from `input-dp.txt`.
- Translates each address using `translate_address`.
- Writes the resulting physical addresses (or `-1` for faults) to `output.txt`.

## Error Handling
- The implementation prints errors encountered during initialization and raises exceptions for critical failures.
- Segment faults and out-of-bounds accesses are handled by returning `-1` as specified.

## Notes
- The simulation assumes that the disk contains valid data for non-resident page tables and pages.
- The logic for loading a page from disk is a placeholder, as the project focuses on address translation and page fault handling.
