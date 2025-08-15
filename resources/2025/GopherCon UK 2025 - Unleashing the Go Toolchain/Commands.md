
```shell
go build
go build -v

time go build
rm main
time go build -v

go build -a -v
go build -a -x

go build
- compile runtime
- compile [...]
- compile main
- link main
  
go help build | grep -A6 toolexec
# Control how the sub go build commands run

go build  -o toolexecwrapper ./cmd/toolexecwrapper/main.go 

go build -toolexec=$PWD/toolexecwrapper .
make demo


go tool compile -V=full
```

