# Placeholder Image Generator

Δημιουργία placeholder εικόνων με συγκεκριμένες διαστάσεις και αναλογίες 

## Usage
Example: Create a placeholder image with a 5/4 aspect ratio and save it in the current directory
```bash
uv run 'https://raw.githubusercontent.com/antsinar/placeholder_image_cli/refs/heads/main/src/placeholdercli.py' ratio --ratio 5 4 --out .
```

Example: Create a 3000x2000px placeholder image with a black color and save it in the current directory
```bash
uv run 'https://raw.githubusercontent.com/antsinar/placeholder_image_cli/refs/heads/main/src/placeholdercli.py' size --width 3000 --height 2000 --color=#000000 --out .
```

## CLI Options
### [mandatory] 
- [X] option: size or ratio
  - size indicates the exact size of the placeholder image
    - requires --width and --height flags to enter dimensions
    - width and height are capped internally in the range of 32, 4000 px
  - ratio indicates the aspect ratio of the image
    - requires the --ratio flag to set the aspect ratio
    - ratio takes a comma separated list of two integers, internally capped in the range of 1, 30
### [optional] 
- [X] color:
  - sets up the background color of the placeholder image
  - used with the -c or --color flag
  - usage -c=<hex_value>
- [X] out:
  - output directory, mandatory if you are executing from a remote source
  - used with the -o or --out flag
  - usage --out <directory_location>