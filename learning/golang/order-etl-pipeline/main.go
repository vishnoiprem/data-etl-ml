package main

import (
    "context"
    "fmt"
)

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create the pipeline: numbers → square → print
    squares := SquareProcessor(ctx, NumberGenerator(1, 2, 3, 4, 5))

    for v := range squares {
        fmt.Println(v)
        if v == 9 { // optional early stop example
            cancel()
            break
        }
    }
}
