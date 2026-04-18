package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"sync"
)

// FileLineGenerator sends all lines from a single file.
func FileLineGenerator(path string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		f, err := os.Open(path)
		if err != nil {
			return
		}
		defer f.Close()
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			out <- scanner.Text()
		}
	}()
	return out
}

// ErrorCounter counts how many lines contain "ERROR".
func ErrorCounter(in <-chan string) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		count := 0
		for line := range in {
			if strings.Contains(line, "ERROR") {
				count++
			}
		}
		out <- count
	}()
	return out
}

// Merge combines multiple result channels into one.
func Merge(channels ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	out := make(chan int)

	output := func(c <-chan int) {
		defer wg.Done()
		for v := range c {
			out <- v
		}
	}

	wg.Add(len(channels))
	for _, c := range channels {
		go output(c)
	}

	go func() {
		wg.Wait()
		close(out)
	}()
	return out
}

func main() {
	files := []string{"app1.log", "app2.log", "app3.log"}

	// Fan‑out: start one processor for each file.
	channels := make([]<-chan int, len(files))
	for i, f := range files {
		channels[i] = ErrorCounter(FileLineGenerator(f))
	}

	// Fan‑in: collect all partial counts.
	total := 0
	for partial := range Merge(channels...) {
		total += partial
	}

	fmt.Printf("Total errors across %d files: %d\n", len(files), total)
}
