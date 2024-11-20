import time
import sys

total_steps = 100
start_time = time.time()

for i in range(1, total_steps + 1):
  # Simulate some processing
  time.sleep(0.1)

  # Calculate progress and ETA
  progress = int((i / total_steps) * 50)  # 50 characters wide progress bar
  completed_percentage = (i / total_steps) * 100
  elapsed_time = time.time() - start_time
  eta = elapsed_time / i * (total_steps - i)

  # Construct progress bar and ETA strings
  progress_bar = f"[{'=' * progress}{'.' * (50 - progress)}]"
  eta_string = f"ETA: {int(eta)}s | Elapsed: {int(elapsed_time)}s"

  # Print progress and ETA
  # print(f"\r{progress_bar} {completed_percentage:.2f}%", end="")
  # print(f"\033[F{eta_string}", end="")
  sys.stdout.write("\033[F\033[K")  # Move cursor up and clear line
  sys.stdout.write("\033[F\033[K")  # Move cursor up and clear line again
  print(progress_bar)
  print(eta_string)

print()  # Move to the next line after the loop completes
