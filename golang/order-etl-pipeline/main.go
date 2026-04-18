package main

import "fmt"

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
	return out
}

// ---------- Processor ----------
// Squares every number it receives.
func SquareProcessor(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			out <- n * n
		}
	}()
	return out
}

// ---------- Consumer ----------
// Prints every value until the channel is closed.
func PrintConsumer(in <-chan int) {
	for n := range in {
		fmt.Println(n)
	}
}

func main() {
	// Connect the pipeline: numbers → square → print
	PrintConsumer(SquareProcessor(NumberGenerator(1, 2, 3, 4, 5)))
}
