#!/usr/bin/env bash
# Join a project's clips, in file-name order, into one video.
# Clips can differ in size, frame rate and whether they have audio; each one is
# normalised to the first clip's size (letterboxed if needed) before joining.
#
# Usage: scripts/assemble.sh projects/<name>
# Output: projects/<name>/final.mp4
set -euo pipefail

project="${1:?usage: scripts/assemble.sh projects/<name>}"
clips_dir="$project/clips"
out="$project/final.mp4"
fps="${FPS:-24}"

command -v ffmpeg >/dev/null || { echo "ffmpeg is not installed" >&2; exit 1; }

mapfile -t clips < <(find "$clips_dir" -maxdepth 1 -type f \
  \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.webm' \) 2>/dev/null | sort -V)
if [ "${#clips[@]}" -eq 0 ]; then
  echo "No clips found in $clips_dir (save them as 01.mp4, 02.mp4, ...)" >&2
  exit 1
fi

build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT

# Target size comes from the first clip, rounded down to even numbers for H.264.
size="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
  -of csv=s=x:p=0 "${clips[0]}")"
w=$(( ${size%x*} / 2 * 2 ))
h=$(( ${size#*x} / 2 * 2 ))
vf="scale=$w:$h:force_original_aspect_ratio=decrease,pad=$w:$h:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=$fps,format=yuv420p"
venc=(-c:v libx264 -preset veryfast -crf 18)
aenc=(-c:a aac -ar 48000 -ac 2 -b:a 192k)

i=0
for clip in "${clips[@]}"; do
  i=$((i + 1))
  part="$build/$(printf '%03d' "$i").mp4"
  dur="$(ffprobe -v error -select_streams v:0 -show_entries format=duration -of csv=p=0 "$clip")"
  if [ -n "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$clip")" ]; then
    ffmpeg -nostdin -y -v error -i "$clip" -vf "$vf" -af apad -t "$dur" \
      "${venc[@]}" "${aenc[@]}" "$part"
  else
    # Add silence so every part has an audio track and they can be joined losslessly.
    ffmpeg -nostdin -y -v error -i "$clip" -f lavfi -i anullsrc=r=48000:cl=stereo \
      -map 0:v -map 1:a -vf "$vf" -t "$dur" "${venc[@]}" "${aenc[@]}" "$part"
  fi
  echo "file '$part'" >> "$build/list.txt"
  echo "  [$i/${#clips[@]}] $(basename "$clip") (${dur%.*}s)"
done

ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$build/list.txt" -c copy -movflags +faststart "$out"
total="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")"
echo "Wrote $out (${w}x${h}, ${total%.*}s)"
