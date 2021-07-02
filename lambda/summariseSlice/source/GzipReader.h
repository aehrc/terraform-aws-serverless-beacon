#include <array>
#include <cstring>
#include <stdio.h>
#include <zlib.h>

class GzipReader
{
    public:
	const unsigned chunkSize;
	char * chunk;
	FILE * inFile;
	gzFile_s * inFile_gz;
	size_t dataToConsume;
	size_t start;
	size_t end;
	bool good;
	public:
	GzipReader(unsigned chunkSize_in)
	:chunkSize(chunkSize_in), chunk(new char[2*chunkSize_in]),dataToConsume(0),start(0),end(0),good(false)
	{}

	int close() {
		return gzclose_r(inFile_gz);
	}
	
	bool open(const char * filename)
	{
        good = ((inFile_gz = gzopen(filename, "rb"))!=NULL);
        return good &= (gzbuffer(inFile_gz,chunkSize)==0);
	}
	
	size_t readIn(char * buf, unsigned bytesToRead)
	{
        return gzread(inFile_gz, buf, bytesToRead);
	}

	char readPastDifferentChars(char c1, char c2)
	{
		start = end;
		do{
			while(end < dataToConsume)
			{
				if(chunk[end]==c1||chunk[end]==c2)
				{
					return chunk[end++];
				}
				end++;
			}
			dataToConsume -= start;
			memcpy(chunk,&chunk[start],dataToConsume);
			end = end-start;
			start = 0;
			if (dataToConsume < chunkSize) {
				size_t newDataToConsume = readIn(chunk+dataToConsume,chunkSize);
				if (newDataToConsume > 0) {
					dataToConsume += newDataToConsume;
				} else {
					break;
				}
			} else {
				break;
			}
		}while(true);
		good = false;
		return '\0';
	}

	template <int N=1>
	bool readPast(char c)
	{
		int num = N;
		start = end;
		do{
			while(end < dataToConsume)
			{
				if(chunk[end++]==c&&((N==1)||(--num==0)))
					return true;
			}
			dataToConsume -= start;
			memcpy(chunk,&chunk[start],dataToConsume);
			end = end-start;
			start = 0;
			if (dataToConsume < chunkSize) {
				size_t newDataToConsume = readIn(chunk+dataToConsume,chunkSize);
				if (newDataToConsume > 0) {
					dataToConsume += newDataToConsume;
				} else {
					break;
				}
			} else {
				break;
			}
		}while(true);
		good = false;
		return false;
	}

	bool readPastAndCheckForCharInBounds(char delim, char lowerBounds, char upperBounds)
	{
		bool flag = false;
		start = end;
		do{
			while(end < dataToConsume)
			{
				if(chunk[end]>=lowerBounds&&chunk[end]<=upperBounds)
					flag = true;
				if(chunk[end++]==delim)
					return flag;
			}
			dataToConsume -= start;
			memcpy(chunk,&chunk[start],dataToConsume);
			end = end-start;
			start = 0;
			if (dataToConsume < chunkSize) {
				size_t newDataToConsume = readIn(chunk+dataToConsume,chunkSize);
				if (newDataToConsume > 0) {
					dataToConsume += newDataToConsume;
				} else {
					break;
				}
			} else {
				break;
			}
		}while(true);
		good = false;
		return false;
	}

	int_fast64_t readPastAndCountChars(char delim)
	{
		int_fast64_t numChars = 0;
		int_fast64_t readChars = 0;
		start = end;
		do{
			while(end < dataToConsume)
			{
				// Gets an idea of the minimum number of characters in any future line
				numChars += 2 * ((chunk[end] == '\t') + (chunk[end] == '/') + (chunk[end] == '|') + (chunk[end] == ';'));
				readChars++;
				if (chunk[end++]==delim)
				{
					std::cout << "readChars: " << readChars << std::endl;
					return numChars;
				}
			}
			dataToConsume -= start;
			memcpy(chunk,&chunk[start],dataToConsume);
			end = end-start;
			start = 0;
			if (dataToConsume < chunkSize) {
				size_t newDataToConsume = readIn(chunk+dataToConsume,chunkSize);
				if (newDataToConsume > 0) {
					dataToConsume += newDataToConsume;
				} else {
					break;
				}
			} else {
				break;
			}
		}while(true);
		good = false;
		return false;
	}

	bool seek(size_t offset)
	{
		start = end;
		do {
			if (end + offset <= dataToConsume) {
				end += offset;
				return true;
			} else {
				offset -= dataToConsume - end;
				end = 0;
				start = 0;
			}
		} while ((dataToConsume = readIn(chunk, chunkSize)));
		good = false;
		return false;
	}

	template <size_t N=1>
	bool skipPast(char c)
	{
		int num = N;
		start = end;
		do{
			while(end < dataToConsume)
			{
				if(chunk[end++]==c&&((N==1)||(--num==0)))
					return true;
			}
			end = 0;
			start = 0;
		}while((dataToConsume = readIn(chunk,chunkSize)));
		good = false;
		return false;
	}

	template <size_t N>
	bool markPositionsWithDifferentChars(char c1, char c2,std::array<size_t,N> &positions)
	{
		start = end;
		int found = 0;
		do{
			while(end < dataToConsume)
			{
				if(chunk[end]==c1 || chunk[end]==c2)
				{
					positions[found++] = end-start;
					end++;
					if(found==N)
						return true;
				}
				end++;
			}
			dataToConsume -= start;
			memcpy(chunk,&chunk[start],dataToConsume);
			end = end-start;
			start = 0;
			if (dataToConsume < chunkSize) {
				size_t newDataToConsume = readIn(chunk+dataToConsume,chunkSize);
				if (newDataToConsume > 0) {
					dataToConsume += newDataToConsume;
				} else {
					break;
				}
			} else {
				break;
			}
		}while(true);
		good = false;
		return false;
	}

	const char* getStartOfRead()
	{
		return &chunk[start];
	}

	size_t getCharactersInRead()
	{
		return good ? (end - start - 1) : end - start;
	}

	bool isGood(){return good;}
};
