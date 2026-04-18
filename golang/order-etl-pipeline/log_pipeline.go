package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
    "sync"
)

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
    // Create sample log files for testing
    files := []string{"app1.log", "app2.log", "app3.log"}
    for _, f := range files {
        os.WriteFile(f, []byte("INFO: started\nERROR: failed\nINFO: ended\n"), 0644)
    }

    channels := make([]<-chan int, len(files))
    for i, f := range files {
        channels[i] = ErrorCounter(FileLineGenerator(f))
    }
    total := 0
    for partial := range Merge(channels...) {
        total += partial
    }
    fmt.Printf("Total errors across %d files: %d\n", len(files), total)
}
