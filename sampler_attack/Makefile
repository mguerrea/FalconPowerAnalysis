NAME = hidden.so

SRCS = hidden.c utils.c
OBJS = $(SRCS:.c=.o)

INC = hidden.h

CC = gcc

CFLAGS = -fPIC -O3
LDFLAGS = -shared


all: $(NAME)

$(NAME): $(OBJS)
	$(CC) ${LDFLAGS} -o $@ $^

$(SRCS:.c=.o):%.o:%.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm $(OBJS)

fclean: clean
	rm $(NAME)
