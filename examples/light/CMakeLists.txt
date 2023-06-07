cmake_minimum_required(VERSION 3.0)
project(light)

# Add the source files to the project
set(SOURCES
    main.c
    light.c
    lib.c
)

# Set the executable name
set(EXECUTABLE_NAME light)

# Add the executable target
add_executable(${EXECUTABLE_NAME} ${SOURCES})

# Add any additional flags or compiler options if needed
# For example, to enable C99 standard:
# target_compile_features(${EXECUTABLE_NAME} PRIVATE c_std_99)

# Add any additional libraries if needed
# For example, to link against the math library:
# target_link_libraries(${EXECUTABLE_NAME} m)
