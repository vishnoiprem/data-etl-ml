package main

import (
	"context"
	"fmt"
	"math/rand"
	"time"
)

func RandomStream() <-chan int {
	out := make(chan int)
	go func() {
		for {
			out <- rand.Intn(1000)
			time.Sleep(100 * time.Millisecond) // slow it down a bit
		}
		// Notice: no close() – this runs until the program stops
	}()
	return out
}

// ---------- Generator ----------
// Sends the given numbers one by one.
func NumberGenerator(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out) // the stage that creates the channel also closes it
		for _, n := range nums {
			out <- n
		}
	}()
	fmt.Println(out)
	return out
}

func SquareProcessor(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case out <- n * n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	squares := SquareProcessor(ctx, NumberGenerator(1, 2, 3))
	for v := range squares {
		fmt.Println(v)
		if v == 4 {
			cancel() // stop early
			break
		}
	}
}
